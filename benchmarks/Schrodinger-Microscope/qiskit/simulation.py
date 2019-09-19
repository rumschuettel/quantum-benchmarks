import matplotlib.pyplot as plt
from experiment import run_experiment_fill_axes

fig = plt.figure(figsize = (12,6))
ax_psps = fig.add_subplot(1,2,1)
ax_zs = fig.add_subplot(1,2,2)
run_experiment_fill_axes(ax_psps, ax_zs, 2, 64, 1024)
plt.show()
