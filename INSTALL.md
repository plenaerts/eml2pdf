# Installation instructions

These instructions are meant to help you on your way if README.md still leaves
some gaps.

**If you are comfortable with a `pip install` you should not read on ;-)**

The preferred way to install packages on your system should be to use some form
of package manager like APT for Debian GNU/Linux and derivatives or DNF for the
Red Hat families, or the Windows Store on Microsoft Windows.

eml2pdf is far from ready to be included in vetted package distributions
such as the official Debian packages as this requires a lot of packaging work
on top of *"just delivering a working script"*.

This is why we currently release eml2pdf via PyPi, the Python Package Index.
Next steps on the roadmap for eml2pdf will be to release packages and
packaged executables next to PyPi and the source packages.

## Installing eml2pdf using pip

The easiest way to install eml2pdf is to install it via pip in a virtual
environment. Pip is the Python package installer. You can find general info on
[the Python documentation pages on installing python modules](
  https://docs.python.org/3/installing/index.html).

On Linux systems you should have **python3** available. On Debian you would
need to install the python3-venv package to create and use virtual
environments. On Windows you can [find Python on the Windows Store](
  https://apps.microsoft.com/search?query=python&hl=nl-nl&gl=BE) and some
help on [Python on Windows for beginners](
  https://learn.microsoft.com/en-us/windows/python/beginners) from Microsoft.

Next you should create a **virtual environment** using
`python3 -m venv <path_to_your_venv_location>`. Basically, virtual environments
create a separate directory with an independent set of Python packages without
polluting your Linux distribution packages. Refer to
[the Python documentation on virtual environments](
  https://docs.python.org/3/library/venv.html#creating-virtual-environments)
for more info on virtual environments.

**Activate your venv** using `source <venv>/bin/activate` on Linux or execute
`<venv>\Scripts\Activate.ps1` in PowerShell on Windows if you are working on
Windows with python3 in the same environment where you have Pango available.
Refer to information below for Windows.

In your shell, you can then issue `pip install eml2pdf` to **install the
latest release** from [PyPI](https://pypi.org), the Python Package Index, or
`pip install <path_to_source_dir>`, which will install the git or other source
pacakge you downloaded and unpacked in the virtual environment.

**The eml2pdf command should now be available in your shell if you activate
your venv.**

## Installing on Windows

Using eml2pdf on Windows should be possible, but it's not easy due to the
Pango dependency. Refer to [weasyprint install instructions for Windows](
  https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)
and then follow the pip installation steps above.

We'll try to make that easier if we get some requests for a packaged Windows
executable.
