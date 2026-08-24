# Sub-keyword Synonym Subtopics Searching (SSSS)
Paper Searching Tool termed as Sub-keyword Synonym Subtopics Searching described in the paper "A review of machine learning in building load prediction", Section 2

Please cite the paper if you use the code for publication:

Zhang, L., Wen, J., Li, Y., Chen, J., Ye, Y., Fu, Y., & Livingood, W. (2021). A review of machine learning in building load prediction. Applied Energy, 285, 116452.

This project is a work-in-progress.

Installation

Download and install [git](https://git-scm.com/download/win)

Download and install the latest version of [Conda](https://docs.conda.io/en/latest/) (version 4.4 or above)

Run Anaconda Prompt as Administrator

Create a new conda environment:

`$ conda create -n <name-of-repository> python=3.6 pip`

`$ conda activate <name-of-repository>`

(If you’re using a version of conda older than 4.4, you may need to instead use source activate <name-of-repository>.)

Ensure that you have navigated to the top level of your cloned repository. You will execute all your pip commands from this location. For example:

`$ cd /path/to/repository`

Install the environment needed for this repository:

`$ pip install -e ".[dev]"`

The core package installs the search, API, PDF, and Zotero dependencies.
The same runtime dependency list is also available in `requirements.txt`.
To include the optional WordCloud workflow, use
`$ pip install -e ".[dev,visualization]"` or
`requirements-visualization.txt`.

API credentials

The Scopus and Elsevier scripts read the API key from the
`ELSEVIER_API_KEY` environment variable. In PowerShell, set it for the
current session before running those scripts:

`$env:ELSEVIER_API_KEY = "your-api-key"`

Before committing, install `pre-commit` in a current Python environment and
run `pre-commit install` followed by `pre-commit run --all-files`.
