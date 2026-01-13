import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
from llm_processor import LLMProcessor
from config_loader import ConfigLoader

st.set_page_config(page_title="Excel AI", layout="wide")

st.title("Excel AI - LLM-Enhanced Spreadsheet Processing")

# Load configuration
config = ConfigLoader()

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'processing_history' not in st.session_state:
    st.session_state.processing_history = []

# File upload
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            file_type = 'csv'
        else:
            df = pd.read_excel(uploaded_file)
            file_type = 'excel'
        
        # Only update if it's a new file
        if st.session_state.original_df is None or uploaded_file.name not in str(st.session_state.get('uploaded_filename', '')):
            st.session_state.df = df.copy()
            st.session_state.original_df = df.copy()
            st.session_state.processing_history = []
            st.session_state.uploaded_filename = uploaded_file.name
        
        st.success(f"File loaded: {uploaded_file.name}")
        st.write(f"Rows: {len(st.session_state.df)}, Columns: {len(st.session_state.df.columns)}")
        
        # Show current dataframe
        with st.expander("View Current Data", expanded=True):
            st.dataframe(st.session_state.df)
        
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")

if st.session_state.df is not None:
    st.divider()
    
    # Show processing history
    if st.session_state.processing_history:
        with st.expander("Processing History"):
            for i, history in enumerate(st.session_state.processing_history, 1):
                st.write(f"**Step {i}:** Added column `{history['column']}` using {history['provider']} ({history['model']})")
    
    # Reset button
    col_reset1, col_reset2 = st.columns([6, 1])
    with col_reset2:
        if st.button("Reset to Original", type="secondary"):
            st.session_state.df = st.session_state.original_df.copy()
            st.session_state.processing_history = []
            st.rerun()
    
    st.divider()
    
    # LLM Configuration
    st.subheader("LLM Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        providers = config.get_providers()
        provider_display = {p: config.get_provider_display_name(p) for p in providers}
        selected_provider = st.selectbox(
            "LLM Provider",
            options=providers,
            format_func=lambda x: provider_display[x]
        )
    
    with col2:
        available_models = config.get_models(selected_provider)
        model_name = st.selectbox("Model", options=available_models)
    
    # Check API key availability
    if config.requires_api_key(selected_provider):
        api_key = config.get_api_key(selected_provider)
        if not api_key:
            st.error(f"API key not found in environment. Set {config.config['llm_providers'][selected_provider]['env_var']} in .env file")
    
    st.divider()
    
    # Column Selection Helper
    st.subheader("Available Columns")
    available_columns = st.session_state.df.columns.tolist()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Use {{column_name}} syntax in prompts. Available: {', '.join(available_columns)}")
    with col2:
        selected_cols_helper = st.multiselect("Quick Insert", available_columns, label_visibility="collapsed")
    
    # Generate column syntax for quick copy
    if selected_cols_helper:
        syntax = " ".join([f"{{{col}}}" for col in selected_cols_helper])
        st.code(syntax, language=None)
    
    st.divider()
    
    # Prompt Configuration
    st.subheader("Prompt Configuration")
    
    system_prompt = st.text_area(
        "System Prompt (can use {column_name} variables)",
        value="You are a helpful assistant that processes data.",
        height=100
    )
    
    user_prompt = st.text_area(
        "User Prompt Template (use {column_name} for variables)",
        value="Process this data: {" + available_columns[0] + "}" if available_columns else "Process this data: {column1}",
        height=150
    )
    
    formatting_instructions = st.text_area(
        "Formatting Instructions",
        value="Return only the processed result without any explanation.",
        height=100
    )
    
    # Extract and validate variables from both prompts
    system_vars = re.findall(r'\{(\w+)\}', system_prompt)
    user_vars = re.findall(r'\{(\w+)\}', user_prompt)
    all_variables = list(set(system_vars + user_vars))
    
    if all_variables:
        st.success(f"Detected variables: {', '.join(all_variables)}")
        
        # Validate variables
        invalid_vars = [v for v in all_variables if v not in available_columns]
        if invalid_vars:
            st.error(f"Invalid column names: {', '.join(invalid_vars)}")
            st.write(f"Available columns: {', '.join(available_columns)}")
    
    st.divider()
    
    # Processing Configuration
    st.subheader("Processing Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        output_column_name = st.text_input("Output Column Name", value="llm_output")
    
    with col2:
        batch_mode = st.selectbox("Processing Mode", ["Batch", "Async Batch", "Sequential"])
    
    with col3:
        batch_size = st.number_input("Batch Size", min_value=1, max_value=100, value=10)
    
    # Check if output column already exists
    if output_column_name in st.session_state.df.columns:
        st.warning(f"Column '{output_column_name}' already exists. It will be overwritten.")
    
    # Process button
    can_process = True
    error_msg = []
    
    if not all_variables:
        can_process = False
        error_msg.append("No variables found in prompts")
    if invalid_vars:
        can_process = False
        error_msg.append("Invalid column names in prompts")
    if config.requires_api_key(selected_provider) and not config.get_api_key(selected_provider):
        can_process = False
        error_msg.append("API key not configured")
    
    if st.button("Process with LLM", type="primary", disabled=not can_process):
        try:
            # Create progress tracking containers
            progress_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                
                with metrics_col1:
                    batch_metric = st.empty()
                with metrics_col2:
                    row_metric = st.empty()
                with metrics_col3:
                    percent_metric = st.empty()
            
            # Progress callback function
            def update_progress(current, total, rows_done, total_rows):
                progress = rows_done / total_rows
                progress_bar.progress(progress)
                
                if batch_mode.lower().replace(" ", "_") == "sequential":
                    status_text.text(f"Processing row {rows_done} of {total_rows}...")
                    batch_metric.metric("Current Row", f"{rows_done}/{total_rows}")
                else:
                    status_text.text(f"Processing batch {current} of {total}...")
                    batch_metric.metric("Batch Progress", f"{current}/{total}")
                
                row_metric.metric("Rows Completed", f"{rows_done}/{total_rows}")
                percent_metric.metric("Completion", f"{progress*100:.1f}%")
            
            # Get credentials from config
            api_key = config.get_api_key(selected_provider) if config.requires_api_key(selected_provider) else None
            base_url = config.get_base_url(selected_provider)
            api_version = config.get_api_version(selected_provider)
            
            # For Azure, get endpoint
            if selected_provider == "azure_openai":
                endpoint = config.get_endpoint(selected_provider)
                if not endpoint:
                    st.error("Azure OpenAI endpoint not found in environment. Set AZURE_OPENAI_ENDPOINT in .env file")
                    st.stop()
                base_url = endpoint
            
            processor = LLMProcessor(
                provider=selected_provider,
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                api_version=api_version
            )
            
            processed_df = processor.process_dataframe(
                df=st.session_state.df,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt,
                formatting_instructions=formatting_instructions,
                output_column=output_column_name,
                mode=batch_mode.lower().replace(" ", "_"),
                batch_size=batch_size,
                progress_callback=update_progress
            )
            
            # Update session state
            st.session_state.df = processed_df
            st.session_state.processing_history.append({
                'column': output_column_name,
                'provider': config.get_provider_display_name(selected_provider),
                'model': model_name,
                'timestamp': datetime.now()
            })
            
            st.success(f"Processing complete! Column '{output_column_name}' added.")
            st.rerun()
                
        except Exception as e:
            st.error(f"Error during processing: {str(e)}")
    
    if not can_process:
        st.error("Cannot process: " + ", ".join(error_msg))

# Display and download processed results
if st.session_state.df is not None and len(st.session_state.processing_history) > 0:
    st.divider()
    st.subheader("Processed Results")
    
    # Download buttons
    col1, col2, col3 = st.columns([2, 2, 3])
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with col1:
        # CSV download
        csv = st.session_state.df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"ai_excel_output_{timestamp}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Excel download
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state.df.to_excel(writer, index=False)
        buffer.seek(0)
        
        st.download_button(
            label="Download as Excel",
            data=buffer,
            file_name=f"ai_excel_output_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col3:
        st.write(f"Total columns: {len(st.session_state.df.columns)} | Rows: {len(st.session_state.df)}")