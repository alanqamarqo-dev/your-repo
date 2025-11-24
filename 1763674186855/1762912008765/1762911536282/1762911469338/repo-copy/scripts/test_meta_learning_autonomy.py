# quick test for MetaLearningEngine autonomous features
from Core_Engines.Meta_Learning import MetaLearningEngine

eng = MetaLearningEngine()

# few-shot examples for a string transform skill (append '!')
batch1 = [("hello", "hello!"), ("world", "world!")]
# second batch adds another example
batch2 = [("test", "test!")]
# holdout
holdout = [("foo", "foo!"), ("bar", "bar!")]

# auto-learn the skill
res = eng.auto_learn_skill('exclaim', batch1)
print('auto learn:', res)

# continual learning over two rounds
history = eng.continual_self_learning('exclaim', [batch1, batch2], rounds=2, eval_holdout=holdout, lr=0.2)
print('history:', history)

# transfer principle to new domain
transfer = eng.transfer_principles_between_domains({'exclaim:append_suffix': 'exclaim_spanish:append_suffix'})
print('transfer:', transfer)

# list principles
print('principles:', eng.list_principles())
