"""Corrected 'Structured Output Validator' code for the Dify code node.

Fixes the defect: the old validator only tested truthiness, so a well-formed
JSON object whose every field was the no-information marker "资料未提及"
validated as a real answer and was shown to the user as a success.

Behaviour kept: on failure return valid="false" with a short error string so the
node routes to "Validation Failed Answer"; signature main(llm_output); output
keys valid, answer_md, error.
"""
import json

CODE = r'''def main(llm_output) -> dict:
    """Validate the LLM's structured diagnosis and render it as markdown.

    Returns valid="false" with a short error string whenever the payload is not
    a usable, grounded answer. "资料未提及" and similar placeholders are NOT
    answers, so a payload made only of them must fail.
    """
    import json
    import re

    # Phrases that mean "the documents did not cover this". Any field whose
    # entire content is one of these is an empty field.
    NO_INFO = (
        "资料未提及",
        "未找到相关技术资料",
        "未找到相关资料",
        "未找到相关文档",
        "无相关信息",
        "无相关资料",
        "无相关文档",
        "无信息",
        "暂无相关资料",
        "暂无相关信息",
        "资料不足",
        "没有相关资料",
        "not mentioned in the material",
        "not mentioned in the provided",
        "no relevant technical document found",
        "no relevant information",
        "no relevant documents",
        "no information available",
        "information not available",
        "not available in the provided",
        "not provided",
        "no documents found",
        "unknown",
        "n/a",
        "none",
    )

    # Words that name a concrete document artifact. Generic words like "文档"
    # are deliberately excluded: "已参考相关文档" names nothing real.
    DOC_HINTS = (
        "manual", "sop", "fault", "parts", "handbook", "datasheet",
        "手册", "说明书", "规程", "案例", "目录", "报告", "图纸", "图册",
    )
    # A real document name ends in a filename or an explicit version.
    DOC_NAME_RE = re.compile(r"\.(txt|pdf|md|docx?|xlsx?|csv)\b|版本\s*v?\d|v\d+\.\d+", re.I)

    def flat(value) -> str:
        """Collapse any field value to a single lowercase string."""
        parts = []

        def walk(item):
            if item is None:
                return
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "content", "value", "name", "title", "document_name"):
                    if key in item:
                        walk(item[key])
                        return
                for sub in item.values():
                    walk(sub)
            elif isinstance(item, (list, tuple, set)):
                for sub in item:
                    walk(sub)
            else:
                parts.append(str(item))

        walk(value)
        return " ".join(parts).strip()

    def normalise(text: str) -> str:
        return re.sub(r"[\s，,。.;；:：、\-—*\[\]{}()（）\u3000]+", "", text).lower()

    def is_placeholder(text: str, allow_tail: bool = True) -> bool:
        """True when a field carries no information at all.

        A marker only counts when it IS the whole value (allowing for
        punctuation/parenthetical wrappers). A sentence that happens to contain
        a marker must not be thrown away.

        `allow_tail=False` is used for source_documents, which must be a list of
        document names: anything starting with a no-information marker is not a
        document name, however long the rest of the sentence is. That catches a
        refusal dressed up as a citation such as
        `资料未提及“远程关机”功能说明，无法据此定位原因（manual-14.txt）`.
        """
        stripped = text.strip()
        if not stripped:
            return True
        if stripped in {"无", "[]", "{}", "-", "null", "none"}:
            return True
        body = normalise(stripped)
        if not body:
            return True
        for phrase in NO_INFO:
            norm = normalise(phrase)
            if not norm:
                continue
            if norm == body:
                return True
            # marker plus only a short qualifier, e.g. 资料未提及（无相关资料）
            idx = body.find(norm)
            if idx == 0 and (not allow_tail or len(body) - len(norm) <= 16):
                return True
        return False

    def as_items(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    if llm_output is None:
        return {"valid": "false", "answer_md": "", "error": "empty_output"}
    if isinstance(llm_output, str):
        if not llm_output.strip():
            return {"valid": "false", "answer_md": "", "error": "empty_output"}

    # --- parse -------------------------------------------------------------
    if isinstance(llm_output, dict):
        data = llm_output
    elif isinstance(llm_output, str):
        text = llm_output.strip()
        data = None
        try:
            data = json.loads(text)
        except Exception:
            # Models sometimes wrap JSON in ```json fences or add prose.
            fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
            candidates = [fenced.group(1)] if fenced else []
            brace = re.search(r"\{.*\}", text, re.S)
            if brace:
                candidates.append(brace.group(0))
            for candidate in candidates:
                try:
                    data = json.loads(candidate.strip())
                    break
                except Exception:
                    continue
            if data is None:
                return {"valid": "false", "answer_md": "", "error": "parse_failed"}
    else:
        return {"valid": "false", "answer_md": "", "error": "not_an_object"}

    if not isinstance(data, dict):
        return {"valid": "false", "answer_md": "", "error": "not_an_object"}

    # --- normalise keys (accept a few benign aliases) ----------------------
    aliases = {
        "possible_causes": ("possible_causes", "causes", "可能原因"),
        "diagnostic_steps": ("diagnostic_steps", "diagnosis_steps", "diagnostic_procedure", "诊断步骤"),
        "repair_procedure": ("repair_procedure", "repair_steps", "维修流程", "维修步骤"),
        "safety_warnings": ("safety_warnings", "安全警告"),
        "source_documents": ("source_documents", "sources", "references", "参考文档"),
    }
    fields = {}
    for canonical, names in aliases.items():
        for name in names:
            if name in data:
                fields[canonical] = data[name]
                break
        fields.setdefault(canonical, None)

    required = ("possible_causes", "diagnostic_steps", "repair_procedure", "source_documents")

    # --- reject a non-answer -----------------------------------------------
    # A field may legitimately be "资料未提及" when the documents really do not
    # cover that aspect, so we do NOT demand every field be substantive - that
    # rejected genuine partial answers. What must never pass is a payload with
    # nothing substantive in it at all (the original bug), or one with no real
    # document named in source_documents (an ungrounded answer).
    ungrounded = []
    substantive_content = []
    for key in ("possible_causes", "diagnostic_steps", "repair_procedure"):
        items = as_items(fields[key])
        substantive = [flat(i) for i in items if flat(i) and not is_placeholder(flat(i))]
        if not substantive:
            ungrounded.append(key)
        else:
            substantive_content.extend(substantive)
    if not substantive_content:
        return {
            "valid": "false",
            "answer_md": "",
            "error": "ungrounded: " + ",".join(ungrounded),
        }

    # --- require at least one real document reference ---------------------
    # An answer with no grounding is exactly what this node exists to stop, so
    # at least one non-placeholder entry must actually name a document.
    sources = [flat(item) for item in as_items(fields["source_documents"])]
    real_sources = []
    for source in sources:
        text = source.strip()
        if not text or is_placeholder(text, allow_tail=False):
            continue
        # Too short/generic to be a document name ("见上文", "参考文档").
        if len(normalise(text)) < 4:
            continue
        named = bool(DOC_NAME_RE.search(text)) or any(hint in text.lower() for hint in DOC_HINTS)
        if named:
            real_sources.append(text)
    if not real_sources:
        if any(s and not is_placeholder(s, allow_tail=False) for s in sources):
            return {"valid": "false", "answer_md": "", "error": "source_documents_not_documents"}
        return {"valid": "false", "answer_md": "", "error": "no_source_documents"}

    # --- render ------------------------------------------------------------
    # A field that is "资料未提及" is still rendered as such: the answer must be
    # explicit that the documents did not cover that aspect.
    causes = [flat(item) for item in as_items(fields["possible_causes"])] or ["资料未提及"]
    steps = [flat(item) for item in as_items(fields["diagnostic_steps"])] or ["资料未提及"]
    repairs = [flat(item) for item in as_items(fields["repair_procedure"])] or ["资料未提及"]
    warnings = [flat(item) for item in as_items(fields["safety_warnings"]) if flat(item)]
    if not warnings:
        warnings = ["无"]

    md = "## 可能原因\n" + "\n".join("- " + x for x in causes)
    md += "\n\n## 诊断步骤\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(steps, 1))
    md += "\n\n## 维修流程\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(repairs, 1))
    md += "\n\n## 安全警告\n" + "\n".join("- " + x for x in warnings)
    md += "\n\n## 参考文档\n" + "\n".join("- " + x for x in real_sources)

    return {"valid": "true", "answer_md": md, "error": ""}
'''


if __name__ == "__main__":
    print(CODE)
