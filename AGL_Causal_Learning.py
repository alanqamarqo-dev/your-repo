class CausalLearningAgent:
    def __init__(self):
        self.causal_graph = {}
    
    def update_belief(self, action, outcome):
        if action in self.causal_graph and outcome in self.causal_graph[action]:
            self.causal_graph[action][outcome] += 1
        else:
            self.causal_graph[action] = {outcome: 1}
    
    def is_safe_action(self, action):
        # Simple loop detection using a set to track visited states
        visited = set()
        stack = [(action, None)]
        
        while stack:
            current_state, previous = stack.pop(0)
            
            if current_state in visited:
                return False
            
            visited.add(current_state)
            
            for next_state in self.causal_graph.get(current_state, {}):
                if next_state != previous:
                    stack.append((next_state, current_state))
        
        return True
    
    def choose_action(self, state):
        # Simple heuristic: choose the action with the highest weight
        best_action = None
        max_weight = 0
        
        for action, outcomes in self.causal_graph.items():
            if state in outcomes and outcomes[state] > max_weight:
                max_weight = outcomes[state]
                best_action = action
        
        return best_action
    
    def self_test(self):
        # Simple loop detection test
        stack = [('A', None)]
        
        while stack:
            current_state, previous = stack.pop(0)
            
            if (current_state, previous) in self.causal_graph or current_state in self.causal_graph and previous in self.causal_graph[current_state]:
                return False
            
            for next_state in self.causal_graph.get(current_state, {}):
                stack.append((next_state, current_state))
        
        return True