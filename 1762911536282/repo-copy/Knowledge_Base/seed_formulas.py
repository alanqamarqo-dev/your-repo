from .Law_Formulas import LawFormula, LawFormulaStore

def load_seed_formulas() -> LawFormulaStore:
    store = LawFormulaStore()
    store.add(LawFormula(
        id="newton2", name="Newton Second Law", domain="physics.mechanics",
        variables=["F","m","a"], equation_str="F - m*a",
        units={"F":"N","m":"kg","a":"m/s^2"}
    ))
    store.add(LawFormula(
        id="ohm", name="Ohm Law", domain="physics.em",
        variables=["V","I","R"], equation_str="V - I*R",
        units={"V":"V","I":"A","R":"Ω"}
    ))
    store.add(LawFormula(
        id="kinetic", name="Kinetic Energy", domain="physics.mechanics",
        variables=["E","m","v"], equation_str="E - (1/2)*m*v**2",
        units={"E":"J","m":"kg","v":"m/s"}
    ))
    return store
