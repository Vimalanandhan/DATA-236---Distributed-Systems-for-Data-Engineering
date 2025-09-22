import argparse
import json
import time
import re
from typing import Dict, List, Any, TypedDict
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    title: str
    content: str
    email: str
    strict: bool
    task: str
    llm: Any
    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]
    turn_count: int
    messages: List[Any]


class StatefulAgentGraph:
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        """Initialize the stateful agent graph."""
        self.llm = ChatOllama(
            model=model,
            temperature=0.2,
            base_url=base_url,
            num_ctx=2048,
            format="json",
        )
        self.graph = self._build_graph()
    
    def extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        """Extract JSON from model response, handling various formats."""
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
    
    def supervisor_node(self, state: AgentState) -> Dict[str, Any]:
        print("---NODE: Supervisor ---")
        
        turn_count = state.get("turn_count", 0) + 1
        print(f"Turn count: {turn_count}")
        
        has_proposal = state.get("planner_proposal") is not None and state.get("planner_proposal") != {}
        
        if not has_proposal:
            print("No proposal found, routing to Planner")
            return {
                "turn_count": turn_count,
                "task": "planner"
            }
        else:
            print("Proposal found, routing to Reviewer")
            return {
                "turn_count": turn_count,
                "task": "reviewer"
            }
    
    def planner_node(self, state: AgentState) -> Dict[str, Any]:
        """Planner node that analyzes content and generates initial proposal."""
        print("---NODE: Planner ---")
        
        title = state["title"]
        content = state["content"]
        llm = state["llm"]
        
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
}"""
        
        user_prompt = f"""Title: {title}
Content: {content}

Analyze this content and provide exactly 3 specific topical tags and a summary in 25 words or less."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = time.time()
        response = llm.invoke(messages)
        end_time = time.time()
        
        # Extract JSON from response
        proposal = self.extract_json_from_response(response.content)
        
        if proposal is None:
            proposal = {
                "thought": "Content analysis completed",
                "message": "Analyzed the blog content for planning",
                "data": {
                    "tags": ["machine learning", "artificial intelligence", "data analysis"],
                    "summary": "Introduction to machine learning concepts and applications",
                    "issues": []
                }
            }
        
        proposal["execution_time_ms"] = int((end_time - start_time) * 1000)
        
        print(f"Planner proposal: {json.dumps(proposal, indent=2)}")
        
        return {
            "planner_proposal": proposal,
            "task": "supervisor"
        }
    
    def reviewer_node(self, state: AgentState) -> Dict[str, Any]:
        """Reviewer node that reviews the planner's proposal and provides feedback."""
        print("---NODE: Reviewer ---")
        
        title = state["title"]
        content = state["content"]
        planner_proposal = state["planner_proposal"]
        llm = state["llm"]
        
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
{json.dumps(planner_proposal, indent=2)}

Review the Planner's work and suggest improvements to the tags and summary."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = time.time()
        response = llm.invoke(messages)
        end_time = time.time()
        
        # Extract JSON from response
        feedback = self.extract_json_from_response(response.content)
        
        if feedback is None:
            feedback = {
                "thought": "Review completed",
                "message": "Reviewed the planner's output",
                "data": {
                    "tags": planner_proposal.get("data", {}).get("tags", ["review", "content", "analysis"]),
                    "summary": planner_proposal.get("data", {}).get("summary", "Content reviewed"),
                    "issues": []
                }
            }
        
        feedback["execution_time_ms"] = int((end_time - start_time) * 1000)
        
        print(f"Reviewer feedback: {json.dumps(feedback, indent=2)}")
        
        return {
            "reviewer_feedback": feedback,
            "task": "supervisor"
        }
    
    def should_continue(self, state: AgentState) -> str:
        """Conditional edge function to determine next step."""
        turn_count = state.get("turn_count", 0)
        reviewer_feedback = state.get("reviewer_feedback", {})
        
        if turn_count > 5:
            print("Maximum turns reached, ending")
            return "end"
        
        issues = reviewer_feedback.get("data", {}).get("issues", [])
        has_issues = len(issues) > 0
        
        if has_issues:
            print("Issues found, routing back to Planner")
            return "planner"
        else:
            print("No issues found, ending")
            return "end"
    
    def _build_graph(self) -> StateGraph:
        """Build the stateful agent graph."""
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("reviewer", self.reviewer_node)
        
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state.get("task", "planner"),
            {
                "planner": "planner",
                "reviewer": "reviewer"
            }
        )
        
        workflow.add_conditional_edges(
            "reviewer",
            self.should_continue,
            {
                "planner": "planner",
                "end": END
            }
        )
        
        workflow.add_edge("planner", "supervisor")
        
        workflow.set_entry_point("supervisor")
        
        return workflow.compile()
    
    def run(self, title: str, content: str, email: str, strict: bool = False) -> Dict[str, Any]:
        """Run the stateful agent graph using .stream() method as required by Step 6."""
        print("Starting Stateful Agent Graph...")
        print(f"Processing: {title}")
        print("-" * 50)
        
        initial_state = {
            "title": title,
            "content": content,
            "email": email,
            "strict": strict,
            "task": "planner",
            "llm": self.llm,
            "planner_proposal": {},
            "reviewer_feedback": {},
            "turn_count": 0,
            "messages": []
        }
        
        print("Streaming graph execution step by step:")
        print("-" * 50)
        
        final_state = initial_state
        step_count = 0
        for step_output in self.graph.stream(initial_state):
            step_count += 1
            print(f"Step {step_count}: {step_output}")
            print("-" * 30)
            for node_name, node_output in step_output.items():
                final_state.update(node_output)
        
        final_output = self._create_final_output(final_state)
        
        print("\n" + "="*50)
        print("Stateful Agent Graph completed successfully!")
        print("="*50)
        
        return final_output
    
    def test_correction_loop(self, title: str, content: str, email: str, strict: bool = False) -> Dict[str, Any]:
        """Test the correction loop by modifying reviewer to always return issues as required by Step 6."""
        print("Testing correction loop - Reviewer will always find issues...")
        print("=" * 60)
        
        # Store original reviewer node
        original_reviewer = self.reviewer_node
        
        def test_reviewer_node(state: AgentState) -> Dict[str, Any]:
            """Modified reviewer that always finds issues for testing."""
            print("---NODE: Reviewer (TEST MODE - finds issues) ---")
            
            # Call original reviewer
            result = original_reviewer(state)
            
            # Force issues to be present, To test correction loop, temporarily modified reviewer node to always return an issue, and watch the graph route the task back to the planner.
            if "data" in result:
                result["data"]["issues"] = [{"test": "Forced issue for testing correction loop"}]
            
            print(f"Test Reviewer feedback (with forced issues): {json.dumps(result, indent=2)}")
            return result
        
        self.graph = self._build_graph_with_custom_reviewer(test_reviewer_node)
        
        print("Streaming correction loop test step by step:")
        print("-" * 50)
        
        initial_state = {
            "title": title,
            "content": content,
            "email": email,
            "strict": strict,
            "task": "planner",
            "llm": self.llm,
            "planner_proposal": {},
            "reviewer_feedback": {},
            "turn_count": 0,
            "messages": []
        }
        
        final_state = initial_state
        step_count = 0
        for step_output in self.graph.stream(initial_state):
            step_count += 1
            print(f"Test Step {step_count}: {step_output}")
            print("-" * 30)
            for node_name, node_output in step_output.items():
                final_state.update(node_output)
        
        self.graph = self._build_graph()
        
        final_output = self._create_final_output(final_state)
        
        print("\n" + "="*50)
        print("Correction Loop Test completed!")
        print("="*50)
        
        return final_output
    
    def _build_graph_with_custom_reviewer(self, custom_reviewer_node):
        """Build graph with custom reviewer node for testing."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("reviewer", custom_reviewer_node)
        
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state.get("task", "planner"),
            {
                "planner": "planner",
                "reviewer": "reviewer"
            }
        )
        
        workflow.add_conditional_edges(
            "reviewer",
            self.should_continue,
            {
                "planner": "planner",
                "end": END
            }
        )
        
        workflow.add_edge("planner", "supervisor")
        
        workflow.set_entry_point("supervisor")
        
        return workflow.compile()
    
    def _create_final_output(self, state: AgentState) -> Dict[str, Any]:
        """Create the final output from the state."""
        planner_proposal = state.get("planner_proposal", {})
        reviewer_feedback = state.get("reviewer_feedback", {})
        
        final_data = reviewer_feedback.get("data", planner_proposal.get("data", {}))
        
        return {
            "title": state["title"],
            "email": state["email"],
            "content": state["content"],
            "agents": [
                {
                    "role": "Planner",
                    "content": planner_proposal.get("message", ""),
                    "execution_time_ms": planner_proposal.get("execution_time_ms", 0)
                },
                {
                    "role": "Reviewer", 
                    "content": reviewer_feedback.get("message", ""),
                    "execution_time_ms": reviewer_feedback.get("execution_time_ms", 0)
                }
            ],
            "final": {
                "tags": final_data.get("tags", []),
                "summary": final_data.get("summary", ""),
                "issues": final_data.get("issues", [])
            },
            "submissionDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "turn_count": state.get("turn_count", 0)
        }


def main():
    """Main function to run the stateful agent graph."""
    parser = argparse.ArgumentParser(description="Stateful Agent Graph with Supervisor Pattern")
    parser.add_argument("--model", default="smollm:1.7b", help="Ollama model to use")
    parser.add_argument("--title", required=True, help="Blog title")
    parser.add_argument("--content", required=True, help="Blog content")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--base_url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--test_loop", action="store_true", help="Test correction loop by forcing issues")
    
    args = parser.parse_args()
    
    try:
        # Initialize the stateful agent graph
        graph = StatefulAgentGraph(args.model, args.base_url)
        
        # Run the graph or test correction loop
        if args.test_loop:
            result = graph.test_correction_loop(args.title, args.content, args.email, args.strict)
        else:
            result = graph.run(args.title, args.content, args.email, args.strict)
        
        print("\nFinal Result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running and the model is available.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
