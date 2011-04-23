import textwrap

def help_para(text) :
    return textwrap.fill(text, 72)

def help_pre (text) :
    return text

def help_header (title) :

    ln = "-" * 72

    return "\n".join([
            ln,
            title.upper(),
            ln
            ])

def help_option (opt, desc, required, indent=0) :

    indent_opt = "\t" * indent
    indent_desc = "\t" * (indent + 1)

    present = "required"

    if not required :
        present = "optional"

    opt = textwrap.fill("* %s (%s)" % (opt, present), 72, initial_indent=indent_opt, subsequent_indent=indent_opt)

    desc = textwrap.fill(desc, 72, initial_indent=indent_desc, subsequent_indent=indent_desc)

    text = "%s\n%s\n" % (opt, desc)

    return text

def help_qa(question, answer) :

    text = "%s\n\n" % question
    text += "%s\n\n" % textwrap.fill(answer, 72, initial_indent="\t", subsequent_indent="\t")

    return text
