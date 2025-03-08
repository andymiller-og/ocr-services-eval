import os
import json
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()


class LLMServices:
    @staticmethod
    def compare_ocr_results(results, model_choice="OpenAI GPT-4o"):
        """
        Compare OCR results using the selected LLM model

        Args:
            results (dict): Dictionary containing OCR results from different services
            model_choice (str): The LLM model to use for comparison

        Returns:
            str: Analysis and comparison of the OCR results
        """
        try:
            # Convert results to a string and chunk it if necessary
            results_str = json.dumps(results, indent=2)
            
            # Create a text splitter for chunking large inputs
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000,
                chunk_overlap=200,
                length_function=len,
            )
            
            # Split the results into chunks
            chunks = text_splitter.split_text(results_str)
            
            # Create a summary of the OCR results for the prompt
            summary = "OCR Results Summary:\n"
            for service_name in results.keys():
                summary += f"- {service_name}: {len(results[service_name])} characters\n"
            
            # Prepare the system prompt
            system_prompt = """You are an expert in OCR technology evaluation. 
            You will be given OCR results from different services for the same document.
            Your task is to compare these results and determine which service performed best.
            Provide a detailed analysis of the strengths and weaknesses of each OCR service.
            Format your response in markdown."""
            
            # Prepare the user prompt
            user_prompt = f"""
            Compare the following OCR services based on their results:
            
            {summary}
            
            I'll provide the detailed results in chunks due to their size.
            
            First chunk of results:
            {chunks[0]}
            """
            
            # Initialize the appropriate LLM based on the model choice
            if model_choice == "OpenAI GPT-4o":
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    return "OpenAI API key not configured in .env file"
                
                llm = ChatOpenAI(
                    model="gpt-4o",
                    temperature=0.7,
                    api_key=api_key
                )
            elif model_choice == "Claude Sonnet 3.5":
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    return "Anthropic API key not configured in .env file"
                
                llm = ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    temperature=0.7,
                    api_key=api_key
                )
            else:
                return f"Unsupported model choice: {model_choice}"
            
            # Create the initial messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Get the initial response
            response = llm.invoke(messages)
            
            # If there are more chunks, continue the conversation
            if len(chunks) > 1:
                for i, chunk in enumerate(chunks[1:], 1):
                    follow_up = f"""
                    Here's chunk {i+1} of the OCR results:
                    
                    {chunk}
                    
                    Please update your analysis based on this additional information.
                    """
                    
                    messages.append(HumanMessage(content=follow_up))
                    response = llm.invoke(messages)
            
            # Return the final response content
            return response.content

        except Exception as e:
            return f"Error comparing OCR results with {model_choice}: {str(e)}"
