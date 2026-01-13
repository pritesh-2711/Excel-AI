# Excel AI

AI-powered spreadsheet processing application that uses LLMs to generate new columns based on existing data.

## Features

- Upload CSV or Excel files
- Configure system prompts and formatting instructions with multi-column support
- Use column names as variables in prompts with `{column_name}` syntax
- Variables supported in both system and user prompts
- Support for multiple LLM providers:
  - Ollama (nemotron-3-nano:30b, llama3.1:latest)
  - OpenAI (gpt-4o, gpt-4o-mini, gpt-4.1 series, gpt-5.1 series, o3/o4 series)
  - Azure OpenAI (same models as OpenAI)
- Three processing modes:
  - Batch processing using LangChain LCEL batch
  - Async batch processing using LangChain LCEL async batch
  - Sequential processing
- Iterative column addition without re-uploading
- Processing history tracking
- Download processed results with timestamp as CSV or Excel

## Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys in `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

Models and providers are configured in `config.yaml`. To add or modify models:

```yaml
llm_providers:
  ollama:
    models:
      - "your-model:tag"
  openai:
    models:
      - "gpt-4o"
```

API keys are read from environment variables. No need to enter them in the UI.

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Using the Application

1. **Upload File**: Upload a CSV or Excel file

2. **Configure LLM**:
   - Select provider from dropdown
   - Select model from dropdown
   - API keys are loaded automatically from environment

3. **Configure Prompts**:
   - **System Prompt**: Set the LLM's behavior (supports variables)
   - **User Prompt Template**: Use `{column_name}` to reference columns
   - **Formatting Instructions**: Specify output format
   - Use the multi-select helper to quickly insert column names

4. **Processing Options**:
   - Set output column name
   - Choose processing mode
   - Set batch size

5. **Process**: Click "Process with LLM" to generate results

6. **Iterate**: Add more columns without re-uploading
   - Current dataframe persists with new columns
   - Processing history is tracked
   - Reset to original with "Reset to Original" button

7. **Download**: Download processed file as CSV or Excel with timestamp

### Example Use Cases

**Sentiment Analysis:**
```
System Prompt: You are a sentiment analysis expert.
User Prompt: Analyze the sentiment of this review: {review_text}
Formatting Instructions: Return only one word: Positive, Negative, or Neutral.
```

**Multi-Column Processing:**
```
System Prompt: You are a product analyst. Focus on {category} products.
User Prompt: Evaluate {product_name} priced at ${price}: {description}
Formatting Instructions: Return a quality score from 1-10.
```

**Iterative Enhancement:**
1. First pass: Generate sentiment from reviews
2. Second pass: Generate summary from original text + sentiment
3. Third pass: Generate recommendations from all previous columns

## LLM Provider Setup

### Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull models:
   - `ollama pull llama3.1:latest`
   - `ollama pull nemotron-3-nano:30b`
3. Ensure Ollama is running (starts automatically)

### OpenAI

1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Set in `.env`: `OPENAI_API_KEY=sk-...`

### Azure OpenAI

1. Create Azure OpenAI resource
2. Deploy a model
3. Set in `.env`:
   - `AZURE_OPENAI_API_KEY=...`
   - `AZURE_OPENAI_ENDPOINT=https://...`

## Project Structure

```
excel-ai/
├── app.py                 # Main Streamlit application
├── llm_processor.py       # LLM processing logic with LangChain LCEL
├── config_loader.py       # Configuration loader
├── config.yaml            # Models and providers configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── sample_data.csv       # Sample data for testing
└── README.md             # This file
```

## Key Features Explained

### Multi-Column Variable Support
Use `{column_name}` in both system and user prompts. The processor automatically detects and validates all variables.

### Iterative Processing
After adding a column, continue working with the updated dataframe. No need to download and re-upload. Processing history shows all added columns.

### Automatic Configuration
API keys, endpoints, and API versions are handled automatically through environment variables and config files. Users only select provider and model.

## Processing Modes

- **Batch**: Processes rows in batches using `chain.batch()` (fastest)
- **Async Batch**: Processes rows asynchronously using `chain.abatch()` (efficient for I/O-bound operations)
- **Sequential**: Processes rows one at a time using `chain.invoke()` (most reliable for unstable connections)

## Requirements

- Python 3.8+
- See `requirements.txt` for package dependencies

## Troubleshooting

**Issue**: "Invalid column names" error
**Solution**: Ensure all `{variables}` in prompt templates match actual column names. Use the quick insert helper.

**Issue**: "API key not found in environment"
**Solution**: Create `.env` file from `.env.example` and add your API keys

**Issue**: Ollama connection error
**Solution**: Verify Ollama is running with `ollama ps`

**Issue**: Column already exists warning
**Solution**: Either choose a different output column name or the existing column will be overwritten

## License

MIT License