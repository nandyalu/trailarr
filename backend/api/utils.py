import inspect
import re


def format_google_docstring(doc: str) -> str:
    if not doc:
        return ""

    doc = inspect.cleandoc(doc)

    # 1. Bold the major sections (Args, Returns)
    headers = ["Args:", "Returns:", "Raises:", "Yields:", "Note:"]
    for header in headers:
        # Using h4-like bolding and spacing
        doc = doc.replace(header, f"\n\n## {header.replace(':', '')}\n")

    lines = doc.split("\n")
    formatted_lines = []

    for line in lines:
        # Match lines starting with 4, 8, or 12 spaces
        match = re.match(r"^(\s{4,})(.*)", line)

        if match:
            spaces = len(match.group(1))
            content = match.group(2).strip()

            if not content:
                continue

            # Case: Main Parameter Line (4 spaces)
            if spaces == 4:
                # Split the arg 'name (type): description'
                # and format as: '**name** (__type__): description'
                if ":" in content:
                    param_part, desc_part = content.split(":", 1)
                    if "(" in param_part and ")" in param_part:
                        # Italicize the type within parentheses
                        name, type_part = param_part.split("(", 1)
                        type_part = type_part.rstrip(")")
                        param_part = (
                            f"**{name.strip()}** (__{type_part.strip()}__)"
                        )
                    else:
                        param_part = f"**{param_part.strip()}**"
                    # Bold the parameter name and type
                    formatted_lines.append(
                        f"- {param_part.strip()}: {desc_part.strip()}"
                    )
                else:
                    formatted_lines.append(f"- {content}")

            # Case: Continuation Line (8+ spaces, like your 'filter' description)
            else:
                # Add two spaces to the previous line for a Markdown line break
                if formatted_lines:
                    formatted_lines[-1] += "  "
                # Indent this line slightly to align under the parameter
                formatted_lines.append(f"  {content}")
        else:
            formatted_lines.append(line)

    return "\n".join(formatted_lines)
