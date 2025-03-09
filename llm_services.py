import os
import json
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
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
            # Create a formatted string with clearly labeled results for each service
            formatted_results = ""
            for service_name, result in results.items():
                formatted_results += f"\n\n### {service_name} Results ###\n\n"
                formatted_results += result
                formatted_results += "\n\n" + "-"*50 + "\n\n"  # Add a separator between services
            
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
            
            # Prepare the user prompt with the clearly labeled results
            user_prompt = f"""
            Compare the following OCR services based on their results:
            
            {summary}
            
            Below are the detailed OCR results from each service. Each service's results are clearly labeled.
            
            {formatted_results}
            
            Please provide a comprehensive analysis of which OCR service performed best and why.
            Consider factors such as:
            1. Text accuracy and correctness
            2. Formatting preservation
            3. Handling of special characters and symbols
            4. Recognition of tables and structured data
            5. Overall completeness of the extracted text
            6. Handling of multi-page documents (if applicable)
            
            For each service, identify specific strengths and weaknesses with examples from the results.
            Conclude with a recommendation of which service would be best for this type of document.
            """
            
            # Initialize the appropriate LLM based on the model choice
            if model_choice == "OpenAI GPT-4o":
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    return "OpenAI API key not configured in .env file"
                
                llm = ChatOpenAI(
                    model="gpt-4o",
                    temperature=0.7,
                    api_key=api_key,
                    max_tokens=4000  # Set a reasonable limit for the response
                )
            elif model_choice == "Claude Sonnet 3.5":
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    return "Anthropic API key not configured in .env file"
                
                llm = ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    temperature=0.7,
                    api_key=api_key,
                    max_tokens=4000  # Set a reasonable limit for the response
                )
            else:
                return f"Unsupported model choice: {model_choice}"
            
            # Create the messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Get the response
            response = llm.invoke(messages)
            
            # Return the response content
            return response.content

        except Exception as e:
            return f"Error comparing OCR results with {model_choice}: {str(e)}"
