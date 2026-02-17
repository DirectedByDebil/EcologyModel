import qsdsan as qs
from qsdsan.processes import create_asm1_cmps, ASM1
import numpy as np


def print_all_saunits():

    print("\n===============================\n");
    
    # Unit operations are modeled as `SanUnit` objects with process and desgin algorithms
    print('`qsdsan` now has the following embedded unit operations:\n')
    for i in dir(qs.sanunits):
        if not i.startswith('_'):
            print(i)


def print_all_processes():
    print("\n===============================\n");
    print(qs.processes.__all__)



def get_rate_function(cmps, asm):
    
    # вектор состояния системы 
    state = np.ones(len(cmps)+1)
    print(state)

    p1 = asm.tuple[0]

    # скорость роста гетеротрофных бактерий при данных концентрациях
    rf = p1.rate_function(state)
    print(rf)
    return rf


def print_unit(unit):
    unit.show()
    print("\n===============================\n")