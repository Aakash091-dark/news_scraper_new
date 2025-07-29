from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import json
import sys
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import HumanMessage, SystemMessage
from pydantic import ValidationError
from typing import Optional
load_dotenv()


def gemini_llm_with_parser(system_role: str, prompt: str, parser: PydanticOutputParser, context: str, max_retries: int) -> Optional[object]:
    
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    format_instructions = parser.get_format_instructions()
    
    # Enhance the prompt with format instructions and context
    enhanced_prompt = f"{prompt}\n\nContext: {context}\n\n{format_instructions}"
    
    for attempt in range(max_retries):
        try:
            
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-2.0-flash-lite",  
                temperature=0.1,             
                max_tokens=65535,             
                google_api_key=GEMINI_API_KEY, 
                timeout=None,
            )
            
            
            messages = [
                SystemMessage(content=system_role),
                HumanMessage(content=enhanced_prompt)
            ]
            
            # FIXED: Use invoke with messages
            response = llm.invoke(messages)

            # FIXED: Correct attribute name
            raw_output = response.content  
            
            

            
            
            # Clean the response if needed
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith('```json'):
                cleaned_output = cleaned_output.replace('```json', '').replace('```', '').strip()
            elif cleaned_output.startswith('```'):
                cleaned_output = cleaned_output.replace('```', '').strip()

            
            parsed_output = parser.parse(cleaned_output)
            
            parsed_json = parsed_output.json() 

            # print(parsed_json)
            # If successful, return the JSON string
            return parsed_json
            
        except ValidationError as e:
            print(f"Attempt {attempt + 1} failed with validation error: {e}")
            if attempt < max_retries - 1:
                # Modify prompt for retry to emphasize format requirements
                enhanced_prompt = f"{prompt}\n\nContext: {context}\n\n{format_instructions}\n\nIMPORTANT: Please ensure your response is valid JSON that exactly matches the required schema. Previous attempt failed validation."
                continue
            else:
                print("All retry attempts failed due to validation errors.")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Attempt {attempt + 1} failed with JSON decode error: {e}")
            print(f"Raw output was: {raw_output}")
            if attempt < max_retries - 1:
                enhanced_prompt = f"{prompt}\n\nContext: {context}\n\n{format_instructions}\n\nIMPORTANT: Please respond with valid JSON only. Do not include any explanatory text before or after the JSON. Do not wrap in markdown code blocks."
                continue
            else:
                print("All retry attempts failed due to JSON parsing errors.")
                return None
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with unexpected error: {e}")
            print(f"Error type: {type(e).__name__}")
            if attempt < max_retries - 1:
                continue
            else:
                print("All retry attempts failed due to unexpected errors.")
                return None
    
    return None



def test_function():
    from pydantic import BaseModel, Field
    from typing import List
    
    class Person(BaseModel):
        name: str = Field(description="Person's name")
        age: int = Field(description="Person's age")
        role: str = Field(description="Person's role")
    
    class Analysis(BaseModel):
        people: List[Person] = Field(description="List of people")
        summary: str = Field(description="Brief summary")
    
    parser = PydanticOutputParser(pydantic_object=Analysis)
    
    result = gemini_llm_with_parser(
        system_role="You are a helpful assistant that extracts structured data.",
        prompt="Extract information about people mentioned in the text.",
        parser=parser,
        context="John, 25, is a developer. Sarah, 30, is a manager.",
        max_retries=3
    )
    
    print("Result:", result)

if __name__ == "__main__":
    test_function()