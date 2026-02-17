import qsdsan as qs
from qsdsan.processes import create_asm1_cmps, ASM1
import biosteam as bst


def get_asm1_cmps():

    asm1_cmps = create_asm1_cmps()

    S_O2 = qs.Component(
        'S_O2', 
        phase='l', 
        formula='O2',

        particle_size='Dissolved gas', 
        degradability='Non',
        organic=False
    )


    cmps = qs.Components([comp for comp in asm1_cmps])
    cmps.append(S_O2)

    cmps.compile(ignore_inaccurate_molar_weight=True)
    
    return cmps


def get_asm1_wastestream():
    
    concentrations = {
        'H2O': 1e6,      # Вода - основа, 1000 кг/м³ = 1e6 г/м³
        'S_S': 200,      # Легкоразлагаемая органика
        'X_S': 150,      # Медленноразлагаемая органика  
        'S_NH': 40,      # Аммоний
        'S_NO': 2,       # Нитраты (мало на входе)
        
        #todo comment this lines
        #'X_BH': 2500,    # Активный ил
        #'X_BA': 150,     # Нитрификаторы
        
        'S_O': 0.5,      # Кислород
        'S_O2': 0.5,
        'S_ALK': 250,    # Щёлочность
        'S_ND': 10,      # Растворённый органический азот
        'X_ND': 5,       # Органический азот в частицах
        'S_I': 30,       # Инертные растворимые вещества
        'X_I': 100,      # Инертные взвешенные вещества
        'S_N2': 15,      # Азот газообразный
    }

    ww = qs.WasteStream('ww')
    ww.set_flow_by_concentration(flow_tot=100, concentrations=concentrations, units=('L/hr', 'mg/L'))

    return ww


def get_asm1_system(ww, cmps):

    asm1 = ASM1()
    #print(asm1.parameters)
    #asm1.show()

    su = qs.sanunits
    A1 = su.CSTR('A1', ins=ww,
        outs='effluent', V=1000, tau=24,  # 24 часа удержания
        process=asm1, suspended_growth_model=asm1)

    # КРИТИЧЕСКИ ВАЖНО: активируем биологический процесс
    A1._suspended_growth = True
    A1._X = {}  # Инициализируем биомассу
    
    # Начальная биомасса в реакторе (г)
    # X_BH ~ 3000 мг/л = 3 г/л * 1000 л = 3000 г
    A1._X['X_BH'] = 3000 # г в реакторе

    #print("process A1: ")
    #print(A1.process)
    #print(A1.ins[0])
    #print(A1.outs[0])


    sys = bst.System('my_sys', path=(A1,))

    sys.set_dynamic_tracker(A1)
    #sys.scope.y0[cmps.index('S_O2')] = 2.0 * A1.V / 1000  # 2 мг/л в г

    sys.isdynamic = True
    sys.simulate(t_span=(0, 50*24), method='BDF', state_reset_hook='reset_cache')

    print("Sys.scope:")

#    print(sys.scope.time_series)
    print(sys.scope.sol)
    #sys.simulate()
    

    return sys, A1


def print_asm1_equations(asm1: ASM1 = None):

    if asm1 is None:
        asm1 = ASM1()

    ids = asm1.IDs
    eq = asm1.rate_equations.rate_equation

    for id in ids:
        print(str(id) + ": " + str(eq[id]))




