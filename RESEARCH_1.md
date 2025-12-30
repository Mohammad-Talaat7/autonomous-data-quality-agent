Libraries: LLM4EDA, lida by Microsoft, LLMAutoEDA (duplicated), klar-EDA, llm4data

# [LLM4EDA](https://github.com/agasheadwait/LLM4EDA)
- Perform exploratory data analysis (EDA) and cleaning using openai API
- Last updated a year ago
### Architecture:
1. Read the data using pandas
2. LangChain to build Agent using Openai api to:
2.1. Perform EDA on the data by executing Python code.
2.2. Clean the data by executing Python code.
2.3. Build classical machine learning models using scikit-learn to make predictions.
### Frameworks:
- pandas
- LangChain
- Scikit-learn
### Features:
- EDA
- LLM Clean based on your prompt
- Classical machine learning models to make predictions.
### AI providers:
- Openai
### Input stream types:
- CSV
### Platforms:
- just a Jupyter Notebook for proof of concept.
### New features requested by users:
- None
### Issues requested by users:
- None

<hr/>

# [lida by Microsoft](https://github.com/microsoft/lida), ([paper](https://aclanthology.org/2023.acl-demo.11.pdf))
- Data visualizations, Data-faithful infographics, Data Summarization
- Last updated a year ago
### Architecture:
1. Read dataset
2. Use LLMX to handel AI APIs
2.1 Perform EDA on the data by executing Python code
2.2 Data Summarization using Predefined templates / prompts
2.2 Get insights about the data from LLMs
### Frameworks:
- pandas
- matplotlib
- seaborn
- plotly
- LLMX (Unified interface to several LLM providers)
- FastAPI
- reactjs
### Features:
- Predefined templates
- Simple UI using reactjs
- Data Summarization
- EDA
- Docker
### AI providers:
- Multiple providers
### Input stream types:
- CSV
### Platforms:
- PyPI (lida)
### New features requested by users:
- Work with PDF files
- AWS Bedrock LLM APIs
### Issues requested by users:
- Needs improvement: Predefined prompts,  Code Executor
- Huggingface models not working

<hr/>

# [LLMAutoEDA](https://github.com/enesmanan/LLMAutoEDA) (duplicated)
- Automated EDA tool powered by Large Language Models, providing in-depth insights and visualizations for your datasets.
- Last updated a year ago
### Architecture:
1. Read dataset
2. Generate html EDA report using Predefined templates and openai API
### Frameworks:
- pandas
- numpy
- ploty
- openai
- prompt-toolkit
- tqdm
### Features:
- Predefined templates
- Full EDA report
### AI providers:
- Openai
### Input stream types:
- CSV
### Platforms:
- PyPI (llm-auto-eda), Jupyter Notebook Generate html file
### New features requested by users:
- Add OLLama support for local models
### Issues requested by users:
- None

<hr/>

# [klar-EDA](https://github.com/klarEDA/klar-EDA)
A python library for automated EDA, with little AI insights
- Last updated 5 months ago
### Architecture:
1. Read dataset
2. Execute predefine python code to generate EDA report
3. Use openai to get insights
### Frameworks:
- tensorflow
- matplotlib
- numpy
- opencv-python
- pandas
- scikit-learn
- seaborn
- Sphinx
- fastapi 
- sqlalchemy 
- scikit-learn
- openai
### Features:
- Automated EDA using python only predefine codes
- Little AI insights
### AI providers:
- Openai
### Input stream types:
- CSV
### Platforms:
- None
### New features requested by users:
- UI using Streamlit or Gradio.
### Issues requested by users:
- None

<hr/>

# [LLM4Data](https://github.com/worldbank/llm4data)
- Development data and knowledge discovery.
- Last updated a year ago
### Architecture:
1. Read the data using sqlalchemy (optional)
2. LangChain to build Agent using Openai api to:
2.1. Generate API URLs and SQL queries using openai
2.2. Execute SQL queries by sqlalchemy
### Frameworks:
- numpy
- pandas
- sqlalchemy
- langchain
- pytest
### Features:
- Generates natural-language-driven API URLs and SQL queries for datasets (e.g., World Development Indicators).
- Metadata augmentation to enhance data context (Explain the dataset).
### AI providers:
- Openai
### Input stream types:
- .db SQLite files (Optional for SQL quires)
### Platforms:
- PyPI (llm4data)
### New features requested by users:
- Multiple providers support
### Issues requested by users:
- None