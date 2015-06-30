__author__ = 'bryan'

import glob
import cPickle as pkl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import ternary as ter
import pandas as pd

def import_files_in_folder(title, quantity, i=None, j=None, base_directory='./'):
    folder_name = base_directory + title + '_' + quantity
    if (i is not None) and (j is not None):
        folder_name += '_' + str(i) + '_' + str(j)
    folder_name += '/'

    data_list = []

    files_to_import = glob.glob(folder_name + '*.pkl')
    for file_path in files_to_import:
        with open(file_path, 'rb') as fi:
            data_list.append(pkl.load(fi))

    # Sort files by radius

    radii = [z['r'] for z in data_list]
    order = np.argsort(radii)
    radii = [radii[z] for z in order]
    data_list = [data_list[z] for z in order]

    return data_list

def get_Fij_at_each_r(title, num_colors, base_directory='./'):
    Fij_dict_list = {}
    for i in range(num_colors):
        for j in range(i, num_colors):
            if i != j:
                Fij_dict_list[i, j] = import_files_in_folder(title, 'Fij_sym', i=i, j=j, base_directory=base_directory)
            else:
                Fij_dict_list[i, j] = import_files_in_folder(title, 'Fij', i=i, j=j, base_directory=base_directory)

    # We now want to organize each of these by radius. UGH.
    # Actually, each thing is sorted by radius. Sooooooo, assuming we do the same
    # radii for each, this isn't too bad.

    num_radii = len(Fij_dict_list[0, 0])

    Fij_at_each_r = []
    for r_index in range(num_radii):
        current_radius_Fij = {}
        for i in range(num_colors):
            for j in range(i, num_colors):
                current_radius_Fij[i, j] = Fij_dict_list[i, j][r_index]
        Fij_at_each_r.append(current_radius_Fij)

    return Fij_at_each_r

def make_x_axis_radians(unit=0.25, pi_range = np.pi):
    const = pi_range / np.pi
    x_tick = np.arange(-const, const+unit, unit)

    x_label = [r"$" + format(r, '.2g')+ r"\pi$" for r in x_tick]
    ax = plt.gca()
    ax.set_xticks(x_tick*np.pi)
    ax.set_xticklabels(x_label)

def make_ternary_plot(input_fracs, label_list, color_list,  r_min=3.5, r_max=10, num_bins=100, offset_list=None):
    if offset_list is None:
        offset_list = [[-15, -7], [-30, 20], [-30, -7]]
    new_r_bins = np.linspace(r_min, r_max, num_bins)

    fig, ax = ter.figure()
    fig.set_size_inches(16, 10)

    plt.hold(True)

    ax.boundary(color='black')
    ax.gridlines(color='black', multiple=0.1)

    groups = input_fracs.groupby('im_set')

    count = 0
    for group_name, cur_data in groups:
        ### Rebin ####
        cur_data = cur_data.loc[cur_data['radius_midbin_scaled'] >= r_min, :]
        cur_data = cur_data.loc[cur_data['radius_midbin_scaled'] <= r_max, :]

        # Rebin
        cut = pd.cut(cur_data['radius_midbin_scaled'], new_r_bins)
        cur_data = cur_data.groupby(cut).agg('mean')

        fracs = cur_data.loc[:, 'ch0':'ch2'].values

        n_colors = fracs.shape[0]
        cmap = sns.cubehelix_palette(as_cmap=True, n_colors=n_colors, light=0.7, dark=.05)

        ax.plot_colored_trajectory(fracs, cmap, alpha=1)
        start_label = None
        finish_label = None
        if (count == len(groups) - 1):
            start_label = 'Start'
            finish_label = 'Finish'

        ax.scatter([fracs[0, :]], s=20, color='red', zorder=99999, marker='o', label=start_label)
        ax.scatter([fracs[-1, :]], s=20, color='black', zorder=99999, marker='o', label=finish_label)

        count += 1

    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)

    plt.xlim(-.1, 1.1)
    plt.ylim(-.07, .93)

    new_ax = plt.gca()

    ter.heatmapping.colorbar_hack(new_ax, r_min, r_max, cmap, text_format='%.2f',
                                 numticks=6)

    ### Create annotations specifying the edges ####

    positions_list = [ter.project_point([1, 0, 0]), ter.project_point([0, 1, 0]),
                 ter.project_point([0, 0, 1])]

    for pos, label, offset, color in zip(positions_list, label_list, offset_list, color_list):
        new_ax.annotate(label, xy=pos, xytext=offset, ha='left',
                        va='top', xycoords='data',
                        textcoords='offset points',
                        fontsize=20, color=color)

    plt.gca().set_aspect('equal')

    plt.legend(loc='best')

    plt.hold(False)

    #plt.savefig('colored_trajectories_radius_labeled.png', dpi=200, bbox_inches='tight')

    #Can we make a heatmap? That would be cool too