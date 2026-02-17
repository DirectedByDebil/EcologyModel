import qsdsan as qs
import qsdsan_asm as qasm
import qsdsan_utils as qu


cmps = qasm.get_asm1_cmps()
#qu.print_unit(cmps)


qs.set_thermo(cmps)

asm1 = qs.processes.ASM1()

qasm.print_asm1_equations()


'''
ww = qasm.get_asm1_wastestream()
#qu.print_unit(ww)

sys, A1 = qasm.get_asm1_system(ww, cmps)
#qu.print_unit(sys)

effluent = A1.outs[0]
'''


# 5. Построй графики:
# - S_F (органика) падает со временем
# - S_NH4 (аммоний) падает
# - X_BH (бактерии) растут
