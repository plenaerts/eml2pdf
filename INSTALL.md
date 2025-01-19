# Installation instructions

These instructions are meant to help you on your way if README.md still leaves
some gaps. If you are comfortable with a `pip install` you should not read on
;-)

The preferred way to install packages on your system should be to use some form
of package manager like APT for debian GNU/Linux and derivatives or DNF for the
Red Hat families, or the Windows Store on Microsoft Windows.

eml_to_pdf is far from ready to be included in for example Debian.

That's why the release page gives packaged executables next to the source
packages.

## Executables

The eml_to_pdf releases provide executable files for Windows and Linux
distributions.

Depending on the security measures on the system where you want to use
eml_to_pdf, those may or may not be an option.

To use an executable, just download it, open a terminal or PowerShell and
invoke the `eml_to_pdf` executable.
Issue `C:\Users\youruser\Downloads\eml_to_pdf-0.8.exe` on Windows, for example.

## Using pip

If the executables are blocked on your system, the next easiest way is to
install python, create a virtual environment (venv) and install this package
from source into this venv.

On Linux systems you should have **python3** available. On Debian you would
need to install the python3-venv package to create and use virtual
environments. On Windows you can [find Python on the Windows Store](
  https://apps.microsoft.com/search?query=python&hl=nl-nl&gl=BE) and some
help on [Python on Windows for beginners](
  https://learn.microsoft.com/en-us/windows/python/beginners) from Microsoft.

Next you should create a **virtual environment** using
`python3 -m venv <path_to_your_venv_location>`. Refer to
[the Python documentation on virtual environments](
  https://docs.python.org/3/library/venv.html#creating-virtual-environments)
for more.

**Activate your venv** using `source <venv>/bin/activate` on Linux or execute
`<venv>\Scripts\Activate.ps1` in PowerShell on Windows.

In your shell, you can then issue `pip install eml_to_pdf` to install the
latest release from [PyPI](https://pypi.org), the Python Package Index, or
`pip install <path_to_source_dir>`, which will install the git or other source
pacakge you downloaded in the virtual environment.

**The eml_to_pdf command should now be available in your activated venv.**
