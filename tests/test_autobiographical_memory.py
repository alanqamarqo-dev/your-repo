import datetime
import json

class AutobiographicalMemory:
    """
    A system to maintain a complete autobiographical record of the system's experiences.
    """
    def __init__(self):
        self.episodes = []
        self.index = {}

    def add_episode(self, description, tags=None, context=None, cause_id=None):
        """
        Records a new episode in the memory.
        """
        timestamp = datetime.datetime.now().isoformat()
        episode_id = len(self.episodes) + 1
        
        episode = {
            "id": episode_id,
            "timestamp": timestamp,
            "description": description,
            "tags": tags or [],
            "context": context or {},
            "cause_id": cause_id  # Link to the cause of this episode
        }
        
        self.episodes.append(episode)
        
        # Simple indexing by tags
        if tags:
            for tag in tags:
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(episode_id)
                
        return episode_id

    def get_causal_chain(self, episode_id):
        """Trace back the chain of causes for a specific episode."""
        chain = []
        current_id = episode_id
        
        while current_id:
            episode = self.get_episode(current_id)
            if not episode:
                break
            chain.append(episode)
            current_id = episode.get("cause_id")
            
        return chain[::-1]  # Return chronological order (Cause -> Effect)

    def get_episode(self, episode_id):
        """Retrieves a specific episode by ID."""
        for ep in self.episodes:
            if ep["id"] == episode_id:
                return ep
        return None

    def find_episodes(self, keyword=None, tag=None):
        """Searches for episodes based on keyword or tag."""
        results = []
        
        if tag and tag in self.index:
            # Fast lookup by tag
            indices = self.index[tag]
            results = [ep for ep in self.episodes if ep["id"] in indices]
            
        elif keyword:
            # Search in description
            results = [ep for ep in self.episodes if keyword.lower() in ep["description"].lower()]
            
        return results

    def get_narrative(self):
        """Returns a summary of the stored autobiography."""
        return f"Autobiography contains {len(self.episodes)} episodes."

print("AutobiographicalMemory class defined successfully.")

# Initialize the memory system
memory_system = AutobiographicalMemory()
print("Memory system initialized.")

# Record some life events
boot_id = memory_system.add_episode(
    "System boot sequence initiated.", 
    tags=["system", "boot"], 
    context={"version": "1.0.0"}
)

math_id = memory_system.add_episode(
    "Solved a complex mathematical problem regarding prime numbers.", 
    tags=["achievement", "math"], 
    context={"difficulty": "high"}
)

error_id = memory_system.add_episode(
    "Encountered a connection timeout while fetching external data.", 
    tags=["error", "network"], 
    context={"retry_count": 3}
)

# Causal link: The optimization was triggered by the math success (hypothetically)
opt_id = memory_system.add_episode(
    "Successfully optimized the self-improvement algorithm.", 
    tags=["achievement", "optimization", "self-improvement"], 
    context={"efficiency_gain": "15%"},
    cause_id=math_id
)

# Causal link: A system crash caused by the network error
crash_id = memory_system.add_episode(
    "System crash due to unhandled network exception.",
    tags=["error", "crash"],
    cause_id=error_id
)

print(f"Recorded {len(memory_system.episodes)} episodes.")

# Test Causal Chain
print("\nTesting Causal Chain for 'System Crash':")
chain = memory_system.get_causal_chain(crash_id)
for step in chain:
    print(f" -> [{step['id']}] {step['description']}")

# Find achievements
achievements = memory_system.find_episodes(tag="achievement")
print(f"Found {len(achievements)} achievements:")
for ach in achievements:
    print(f" - [{ach['timestamp']}] {ach['description']}")

# Find errors
errors = memory_system.find_episodes(keyword="timeout")
print(f"\nFound {len(errors)} errors related to 'timeout':")
for err in errors:
    print(f" - {err['description']}")

# Direct inspection
total_memories = len(memory_system.episodes)
expected_memories = 5

assert total_memories == expected_memories, f"Expected {expected_memories} memories, found {total_memories}"

print("Persistence verification passed: All memories are accounted for.")
print(json.dumps(memory_system.episodes, indent=2))

# Basic stats
print(memory_system.get_narrative())

tags_count = len(memory_system.index)
print(f"Total unique tags used: {tags_count}")
print(f"Tags: {list(memory_system.index.keys())}")
