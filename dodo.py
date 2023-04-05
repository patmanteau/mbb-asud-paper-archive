from doit.tools import result_dep, create_folder
from pathlib import Path
import shutil
import subprocess

PROJ_NAME = "mbb-asud-paper"

BIB_NAME = f"{PROJ_NAME}.bib"

BASE_DIR = Path(".")
SOURCE_DIR = BASE_DIR / "src"
BUILD_DIR = BASE_DIR / "build"
TEST_DIR = BASE_DIR / "test"
TOOLS_DIR = BASE_DIR / "tools"

MD_SOURCE_DIR = SOURCE_DIR / "md"
ASSET_SOURCE_DIR = SOURCE_DIR / "assets"
LATEX_SOURCE_DIR = SOURCE_DIR / "latex"

MD_BUILD_DIR = BUILD_DIR / "md"
ASSET_BUILD_DIR = BUILD_DIR / "assets"
TYPST_BUILD_DIR = BUILD_DIR / "typst"
LATEX_BUILD_DIR = BUILD_DIR / "latex"
HTML_BUILD_DIR = BUILD_DIR / "html"

TYPST_FONT_DIR = SOURCE_DIR / "fonts"


class ToolPandoc:
    CMD = "pandoc"
    DEPS = ["metadata.yaml"]


class ToolTypst:
    CMD = "typst"
    DEPS = []


class IntoLatex:
    CMD = ToolPandoc.CMD
    DEFAULTS_PATH = "defaults_latex.yaml"
    ARGS = [f"--defaults={DEFAULTS_PATH}"]
    DEPS = [*ToolPandoc.DEPS, DEFAULTS_PATH]


class IntoHtml:
    CMD = ToolPandoc.CMD
    DEFAULTS_PATH = "defaults_html.yaml"
    ARGS = [f"--defaults={DEFAULTS_PATH}"]
    DEPS = []


class IntoTypst:
    CMD = ToolPandoc.CMD
    DEFAULTS_PATH = "defaults_typst.yaml"
    ARGS = [f"--defaults={DEFAULTS_PATH}"]
    DEPS = [*ToolPandoc.DEPS, DEFAULTS_PATH]


class IntoTypstPdf:
    CMD = ToolTypst.CMD
    ARGS = ["--font-path", f"{TYPST_FONT_DIR}"]
    DEPS = [*ToolTypst.DEPS]


class MakePdf:
    CMD = "latexmk"
    ARGS = [
        "-r",
        LATEX_BUILD_DIR / "latexmkrc",
        # '-outdir={}/latex'.format(BUILD_DIR),
        "-lualatex",
        # '-pdflualatex=luahblatex',
        "-bibtex",
        "-shell-escape",
        "-quiet",
        "-cd",
        "-time",
    ]


class FilterLog:
    CMD = "gawk"
    ARGS = ["-f", "{}".format(TOOLS_DIR / "latex-errorfilter.awk")]


DOIT_CONFIG = {
    "default_tasks": ["make_pdf", "filter_log", "copy_pdf"],
    "cleanforget": True,
    "action_string_formatting": "new",
}


def do_cp(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def do_cp_R(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return True


def do_rmtree(path):
    shutil.rmtree(path, ignore_errors=True)
    return True


def do_filter_log(src, dst):
    out = subprocess.run(
        [FilterLog.CMD, *FilterLog.ARGS, str(src)],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )
    with open(dst, mode="wb") as f:
        f.write(out.stdout)
    return True


def task_copy_bib():
    """Copy bibliography file to the build tree"""

    bibsrc = SOURCE_DIR / BIB_NAME
    target = BUILD_DIR / BIB_NAME

    return {
        "actions": [
            (do_cp, [bibsrc, target]),
        ],
        "file_dep": [bibsrc],
        "targets": [target],
    }


def task_copy_typst_template():
    """Copy bibliography file to the build tree"""

    src = SOURCE_DIR / "template.typst"
    target = BUILD_DIR / "template.typst"

    return {
        "actions": [
            (do_cp, [src, target]),
        ],
        "file_dep": [src],
        "targets": [target],
    }


def task_copy_assets():
    """Copy asset files to the build tree"""

    asset_files = ASSET_SOURCE_DIR.glob("**/*")

    for asset_file in asset_files:
        target = ASSET_BUILD_DIR / asset_file.relative_to(ASSET_SOURCE_DIR)
        yield {
            "name": asset_file.name,
            "actions": [(do_cp, [asset_file, target])],
            "file_dep": [ASSET_SOURCE_DIR / asset_file.name],
            "targets": [target],
        }


def task_copy_latex():
    """Copy latex files to the build tree"""

    for latex_file in [f for f in LATEX_SOURCE_DIR.glob("**/*") if f.is_file()]:
        # rename target file if needed
        if latex_file.name == "texplate.tex":
            target = LATEX_BUILD_DIR / latex_file.relative_to(LATEX_SOURCE_DIR)
            target = target.parent / "{}.tex".format(PROJ_NAME)
        elif latex_file.name == "texplate.xmpdata":
            target = LATEX_BUILD_DIR / latex_file.relative_to(LATEX_SOURCE_DIR)
            target = target.parent / "{}.xmpdata".format(PROJ_NAME)
        else:
            target = LATEX_BUILD_DIR / latex_file.relative_to(LATEX_SOURCE_DIR)

        yield {
            "name": latex_file.name,
            "actions": [
                (do_cp, [latex_file, target]),
            ],
            "file_dep": [latex_file],
            "targets": [target],
        }


def task_copy_html():
    """Copy html template to the build tree"""

    template_src_dir = SOURCE_DIR / "templates" / "pandoc-uikit"

    template_files = [
        template_src_dir / f
        for f in [
            "jquery.sticky-kit.js",
            "scripts.js",
            "style.css",
            "uikit.css",
            "uikit.js",
        ]
    ]

    for template_file in template_files:
        yield {
            "name": template_file.name,
            "actions": [
                (do_cp, [template_file, HTML_BUILD_DIR / template_file.name]),
            ],
            "file_dep": [template_file],
            "targets": [HTML_BUILD_DIR / template_file.name],
        }


def from_defaults(path="defaults_latex.yaml"):
    import yaml

    # get template and list of filters from defaults yaml
    template = ""
    filters = []
    with open(path, "r") as f:
        defaults = yaml.load(f, Loader=yaml.FullLoader)
        template = defaults["template"]
        filters = defaults["filters"]
    return (template, filters)


def task_into_latex():
    """Markdown > Pandoc > LaTeX"""

    source_files = sorted(list((MD_SOURCE_DIR).glob("**/*.md")))
    target = LATEX_BUILD_DIR / "pandoc.tex"

    (template, filters) = from_defaults(IntoLatex.DEFAULTS_PATH)

    return {
        "actions": [
            (create_folder, [LATEX_BUILD_DIR]),
            [
                IntoLatex.CMD,
                *IntoLatex.ARGS,
                "--output={}".format(target),
                *source_files,
            ],
        ],
        "file_dep": [*source_files, template, *filters],
        "targets": [target],
    }


def task_into_typst():
    """Runs pandoc to generate typst file"""

    source_files = sorted(list((MD_SOURCE_DIR).glob("**/*.md")))
    target = TYPST_BUILD_DIR / f"{PROJ_NAME}.typst"

    # (template, filters) = from_defaults(IntoTypst.DEFAULTS_PATH)

    return {
        "actions": [
            (create_folder, [TYPST_BUILD_DIR]),
            [
                IntoTypst.CMD,
                *IntoTypst.ARGS,
                f"--output={target}",
                *source_files,
            ],
        ],
        "file_dep": [*IntoTypst.DEPS, *source_files],
        "targets": [target],
    }


def task_into_typst_pdf():
    """Runs typst to generate pdf"""

    dep = TYPST_BUILD_DIR / f"{PROJ_NAME}.typst"
    bib = SOURCE_DIR / f"{PROJ_NAME}.bib"
    target = TYPST_BUILD_DIR / f"{PROJ_NAME}-typst.pdf"

    return {
        "actions": [
            (create_folder, [TYPST_BUILD_DIR]),
            (do_cp, [bib, TYPST_BUILD_DIR / bib.name]),
            [IntoTypstPdf.CMD, *IntoTypstPdf.ARGS, str(dep), str(target)],
        ],
        "file_dep": [*IntoTypstPdf.DEPS, dep, bib],
        "targets": [target],
    }


# def task_test_into_latex():
#     """Markdown test document > Pandoc > LaTeX"""

#     source_files = sorted(list((TEST_DIR / 'md').glob('**/*.md')))
#     target = BUILD_DIR / 'latex' / 'pandoc.tex'

#     return {
#         'actions': [
#             (create_folder, [BUILD_DIR / 'latex']),
#             [
#                 IntoLatex.CMD,
#                 *IntoLatex.ARGS,
#                 '--template={}'.format(IntoLatex.TEMPLATE),
#                 *['--lua-filter={}'.format(flt) for flt in IntoLatex.LUA_FILTERS],
#                 *['--filter={}'.format(flt) for flt in IntoLatex.FILTERS],
#                 '--output={}'.format(target),
#                 *source_files
#             ]
#         ],
#         'file_dep': [
#             *source_files,
#             IntoLatex.TEMPLATE,
#             *IntoLatex.LUA_FILTERS,
#             *IntoLatex.FILTERS
#         ],
#         'targets': [target]
#     }


def task_into_html():
    """Markdown > Pandoc > HTML"""

    source_files = sorted(list((SOURCE_DIR / "md").glob("**/*.md")))
    target = HTML_BUILD_DIR / f"{PROJ_NAME}.html"

    (template, filters) = from_defaults(IntoHtml.DEFAULTS_PATH)

    return {
        "actions": [
            (create_folder, [HTML_BUILD_DIR]),
            [IntoHtml.CMD, *IntoHtml.ARGS, f"--output={target}", *source_files],
        ],
        "file_dep": [*source_files, template, *filters],
        "uptodate": [result_dep("copy_html")],
        "targets": [target],
    }


def task_make_pdf():
    """Runs latexmk"""

    pdf = LATEX_BUILD_DIR / "{}.pdf".format(PROJ_NAME)
    return {
        "actions": [
            (create_folder, [LATEX_BUILD_DIR]),
            [
                MakePdf.CMD,
                *MakePdf.ARGS,
                "{}/latex/{}.tex".format(BUILD_DIR, PROJ_NAME),
            ],
        ],
        "uptodate": [
            result_dep("copy_assets"),
            result_dep("copy_latex"),
            result_dep("into_latex"),
        ],
        "clean": [(do_rmtree, [BUILD_DIR])],
        "targets": [pdf],
    }


# def task_make_typst():
#     """Runs pandoc to generate typst file"""
#     dep = SOURCE_DIR / f"{PROJ_NAME}.md"
#     target = BUILD_DIR / f"{PROJ_NAME}.typst"
#     return {
#         "actions": [f"pandoc -f markdown -i {dep} -t typst -o {target}"],
#         "file_dep": [dep],
#         "targets": [target],
#     }


# def task_make_test_pdf():
#     """Runs latexmk on a test document"""

#     pdf = BUILD_DIR / 'latex' / '{}-test.pdf'.format(PROJ_NAME)
#     return {
#         'actions': [
#             (create_folder, [BUILD_DIR / 'latex']),
#             [
#                 MakePdf.CMD,
#                 *MakePdf.ARGS,
#                 '{}/latex/{}.tex'.format(BUILD_DIR, PROJ_NAME)
#             ],
#         ],
#         'uptodate': [
#             result_dep('copy_assets'),
#             result_dep('copy_latex'),
#             result_dep('test_into_latex')
#         ],
#         'clean': [
#             (do_rmtree, [BUILD_DIR])
#         ],
#         'targets': [pdf]
#     }


def task_filter_log():
    """Makes LaTeX's log file a bit more palpable"""

    log = LATEX_BUILD_DIR / "{}.log".format(PROJ_NAME)
    filtered_log = BUILD_DIR / "{}-latex.log".format(PROJ_NAME)

    return {
        "actions": [(do_filter_log, [log, filtered_log]), ["cat", filtered_log]],
        "file_dep": [log],
    }


def task_copy_pdf():
    """Copies the compiled PDF to its final location"""

    pdf = LATEX_BUILD_DIR / "{}.pdf".format(PROJ_NAME)
    dst = BUILD_DIR / pdf.name
    return {"actions": [(do_cp, [pdf, dst])], "file_dep": [pdf]}
