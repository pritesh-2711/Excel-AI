import pandas as pd
import asyncio
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_ollama import OllamaLLM

class LLMProcessor:
    def __init__(self, provider: str, model_name: str, api_key: str = None, 
                 base_url: str = None, api_version: str = None):
        """
        Initialize LLM processor with specified provider
        
        Args:
            provider: One of 'ollama', 'openai', 'azure_openai'
            model_name: Model name or deployment name
            api_key: API key for OpenAI/Azure
            base_url: Base URL for Ollama or Azure endpoint
            api_version: API version for Azure
        """
        self.provider = provider
        self.model_name = model_name
        
        if provider == "ollama":
            self.llm = OllamaLLM(
                model=model_name,
                base_url=base_url
            )
        elif provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                temperature=0
            )
        elif provider == "azure_openai":
            self.llm = AzureChatOpenAI(
                deployment_name=model_name,
                api_key=api_key,
                azure_endpoint=base_url,
                api_version=api_version,
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def create_chain(self, system_prompt: str, user_prompt_template: str, 
                     formatting_instructions: str):
        """Create LCEL chain with prompts"""
        
        full_system_prompt = f"{system_prompt}\n\n{formatting_instructions}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", full_system_prompt),
            ("user", user_prompt_template)
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain
    
    def prepare_inputs(self, df: pd.DataFrame, system_prompt: str, user_prompt_template: str) -> List[Dict]:
        """Prepare input dictionaries for batch processing from both system and user prompts"""
        import re
        
        # Extract variables from both system and user prompts
        system_vars = re.findall(r'\{(\w+)\}', system_prompt)
        user_vars = re.findall(r'\{(\w+)\}', user_prompt_template)
        all_variables = list(set(system_vars + user_vars))
        
        inputs = []
        for _, row in df.iterrows():
            input_dict = {}
            for var in all_variables:
                if var in df.columns:
                    input_dict[var] = str(row[var]) if pd.notna(row[var]) else ""
                else:
                    input_dict[var] = ""
            inputs.append(input_dict)
        
        return inputs
    
    def process_dataframe(self, df: pd.DataFrame, system_prompt: str, 
                         user_prompt_template: str, formatting_instructions: str,
                         output_column: str = "llm_output", mode: str = "batch",
                         batch_size: int = 10, progress_callback=None) -> pd.DataFrame:
        """
        Process dataframe with LLM
        
        Args:
            df: Input dataframe
            system_prompt: System prompt for LLM (can contain variables)
            user_prompt_template: User prompt template with {variables}
            formatting_instructions: Additional formatting instructions
            output_column: Name of output column
            mode: Processing mode ('batch', 'async_batch', 'sequential')
            batch_size: Batch size for processing
            progress_callback: Optional callback function(current, total, rows_done, total_rows)
            
        Returns:
            DataFrame with new output column
        """
        
        chain = self.create_chain(system_prompt, user_prompt_template, formatting_instructions)
        inputs = self.prepare_inputs(df, system_prompt, user_prompt_template)
        
        if mode == "batch":
            outputs = self._batch_process(chain, inputs, batch_size, progress_callback)
        elif mode == "async_batch":
            outputs = self._async_batch_process(chain, inputs, batch_size, progress_callback)
        else:  # sequential
            outputs = self._sequential_process(chain, inputs, progress_callback)
        
        # Create result dataframe
        result_df = df.copy()
        result_df[output_column] = outputs
        
        return result_df
    
    def _batch_process(self, chain, inputs: List[Dict], batch_size: int, progress_callback=None) -> List[str]:
        """Process in batches using LCEL batch"""
        outputs = []
        total_batches = (len(inputs) + batch_size - 1) // batch_size
        
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            batch_outputs = chain.batch(batch)
            outputs.extend(batch_outputs)
            
            if progress_callback:
                current_batch = (i // batch_size) + 1
                progress_callback(current_batch, total_batches, len(outputs), len(inputs))
        
        return outputs
    
    def _async_batch_process(self, chain, inputs: List[Dict], batch_size: int, progress_callback=None) -> List[str]:
        """Process in batches using async LCEL"""
        
        async def process_async():
            outputs = []
            total_batches = (len(inputs) + batch_size - 1) // batch_size
            
            for i in range(0, len(inputs), batch_size):
                batch = inputs[i:i + batch_size]
                batch_outputs = await chain.abatch(batch)
                outputs.extend(batch_outputs)
                
                if progress_callback:
                    current_batch = (i // batch_size) + 1
                    progress_callback(current_batch, total_batches, len(outputs), len(inputs))
            
            return outputs
        
        return asyncio.run(process_async())
    
    def _sequential_process(self, chain, inputs: List[Dict], progress_callback=None) -> List[str]:
        """Process sequentially using LCEL invoke"""
        outputs = []
        total_rows = len(inputs)
        
        for idx, input_dict in enumerate(inputs, 1):
            output = chain.invoke(input_dict)
            outputs.append(output)
            
            if progress_callback:
                progress_callback(idx, total_rows, idx, total_rows)
        
        return outputs