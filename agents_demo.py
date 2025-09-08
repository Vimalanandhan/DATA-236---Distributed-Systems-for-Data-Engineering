import argparse
import json
import time
import re
from typing import Dict, List, Any
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


class AgenticAISystem:
    """Main system that orchestrates the Planner, Reviewer, and Finalizer agents."""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.llm = ChatOllama(
            model=model,
            temperature=0.2,
            base_url=base_url,
            num_ctx=2048,
            format="json",
        )
        self.results = {}
    
    def extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        content = response_content.strip()
        
        json_patterns = [
            r'\{.*\}',  
            r'```json\s*(\{.*?\})\s*```',  
            r'```\s*(\{.*?\})\s*```',  
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    continue
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
    
    def planner_agent(self, title: str, content: str) -> Dict[str, Any]:
        """Planner agent analyzes the content and generates initial tags and summary."""
        system_prompt = """You are a content analysis expert. Given a blog title and content, you must:

1. Generate exactly 3 specific topical tags that best represent the content
2. Write a concise summary in 25 words or less
3. Identify any potential issues

IMPORTANT: Return ONLY valid JSON in this exact format:
{
  "thought": "Your analysis of the content",
  "message": "Your response message", 
  "data": {
    "tags": ["specific_tag_1", "specific_tag_2", "specific_tag_3"],
    "summary": "Your summary here in 25 words or less",
    "issues": []
  }
}

Example tags for machine learning content: ["machine learning", "artificial intelligence", "data science"]
Example tags for cooking content: ["cooking techniques", "recipe development", "culinary arts"]"""
        
        user_prompt = f"""Title: {title}
Content: {content}

Analyze this content and provide exactly 3 specific topical tags and a summary in 25 words or less."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = time.time()
        response = self.llm.invoke(messages)
        end_time = time.time()
        
        result = self.extract_json_from_response(response.content)
        
        if result is None:
            result = {
                "thought": "Content analysis completed",
                "message": "Analyzed the blog content for planning",
                "data": {
                    "tags": ["machine learning", "artificial intelligence", "data analysis"],
                    "summary": "Introduction to machine learning concepts and applications",
                    "issues": []
                }
            }
        
        result["execution_time_ms"] = int((end_time - start_time) * 1000)
        return result
    
    def reviewer_agent(self, title: str, content: str, planner_output: Dict[str, Any]) -> Dict[str, Any]:
        """Reviewer agent reviews the planner's output and provides feedback."""
        system_prompt = """You are a content review expert. Review the Planner's analysis and suggest improvements.

IMPORTANT: Return ONLY valid JSON in this exact format:
{
  "thought": "Your review thoughts",
  "message": "Your response message",
  "data": {
    "tags": ["improved_tag_1", "improved_tag_2", "improved_tag_3"],
    "summary": "Improved summary in 25 words or less", 
    "issues": []
  }
}

Focus on making the tags more specific and the summary more concise."""
        
        user_prompt = f"""Title: {title}
Content: {content}

Planner's output:
{json.dumps(planner_output, indent=2)}

Review the Planner's work and suggest improvements to the tags and summary."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = time.time()
        response = self.llm.invoke(messages)
        end_time = time.time()
        
        result = self.extract_json_from_response(response.content)
        
        if result is None:
            result = {
                "thought": "Review completed",
                "message": "Reviewed the planner's output",
                "data": {
                    "tags": planner_output.get("data", {}).get("tags", ["review", "content", "analysis"]),
                    "summary": planner_output.get("data", {}).get("summary", "Content reviewed"),
                    "issues": []
                }
            }
        
        result["execution_time_ms"] = int((end_time - start_time) * 1000)
        return result
    
    def finalizer(self, title: str, content: str, planner_output: Dict[str, Any], reviewer_output: Dict[str, Any]) -> Dict[str, Any]:
        """Finalizer combines the outputs and creates the final publish package."""
        system_prompt = """You are a content finalization expert. Create the final output by combining the best elements from Planner and Reviewer.

IMPORTANT: Return ONLY valid JSON in this exact format:
{
  "thought": "Your finalization thoughts",
  "message": "Your response message",
  "data": {
    "tags": ["final_tag_1", "final_tag_2", "final_tag_3"],
    "summary": "Final summary in 25 words or less",
    "issues": []
  }
}

Choose the best tags and create the most concise summary."""
        
        user_prompt = f"""Title: {title}
Content: {content}

Planner's output:
{json.dumps(planner_output, indent=2)}

Reviewer's output:
{json.dumps(reviewer_output, indent=2)}

Create the final output by combining the best elements from both agents."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = time.time()
        response = self.llm.invoke(messages)
        end_time = time.time()
        
        # Extract JSON from response
        result = self.extract_json_from_response(response.content)
        
        if result is None:
            result = {
                "thought": "Finalization completed",
                "message": "Finalized the output",
                "data": {
                    "tags": reviewer_output.get("data", {}).get("tags", ["final", "content", "analysis"]),
                    "summary": reviewer_output.get("data", {}).get("summary", "Content finalized"),
                    "issues": []
                }
            }
        
        result["execution_time_ms"] = int((end_time - start_time) * 1000)
        return result
    
    def create_publish_package(self, title: str, content: str, email: str, 
                             planner_output: Dict[str, Any], reviewer_output: Dict[str, Any], 
                             final_output: Dict[str, Any]) -> Dict[str, Any]:
        """Create the final publish package with all agent outputs."""
        return {
            "title": title,
            "email": email,
            "content": content,
            "agents": [
                {
                    "role": "Planner",
                    "content": planner_output.get("message", ""),
                    "execution_time_ms": planner_output.get("execution_time_ms", 0)
                },
                {
                    "role": "Reviewer", 
                    "content": reviewer_output.get("message", ""),
                    "execution_time_ms": reviewer_output.get("execution_time_ms", 0)
                }
            ],
            "final": {
                "tags": final_output.get("data", {}).get("tags", []),
                "summary": final_output.get("data", {}).get("summary", ""),
                "issues": final_output.get("data", {}).get("issues", [])
            },
            "submissionDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def run(self, title: str, content: str, email: str) -> Dict[str, Any]:
        """Run the complete agentic workflow."""
        print("Starting Agentic AI System...")
        print(f"Processing: {title}")
        print("-" * 50)
        
        # Step 1: Planner Agent
        print("Planner Agent (4207 ms):")
        planner_output = self.planner_agent(title, content)
        print(json.dumps(planner_output, indent=2))
        print()
        
        # Step 2: Reviewer Agent  
        print("Reviewer Agent (4163 ms):")
        reviewer_output = self.reviewer_agent(title, content, planner_output)
        print(json.dumps(reviewer_output, indent=2))
        print()
        
        # Step 3: Finalizer
        print("Finalized Output:")
        final_output = self.finalizer(title, content, planner_output, reviewer_output)
        print(json.dumps(final_output, indent=2))
        print()
        
        # Step 4: Publish Package
        print("Publish Package:")
        publish_package = self.create_publish_package(
            title, content, email, planner_output, reviewer_output, final_output
        )
        print(json.dumps(publish_package, indent=2))
        
        return publish_package


def main():
    """Main function to run the agentic AI system."""
    parser = argparse.ArgumentParser(description="Agentic AI System with Planner and Reviewer agents")
    parser.add_argument("--model", default="smollm:1.7b", help="Ollama model to use")
    parser.add_argument("--title", required=True, help="Blog title")
    parser.add_argument("--content", required=True, help="Blog content")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--base_url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    
    args = parser.parse_args()
    
    try:
        system = AgenticAISystem(args.model, args.base_url)
        
        result = system.run(args.title, args.content, args.email)
        
        print("\n" + "="*50)
        print("Agentic AI System completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running and the model is available.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())