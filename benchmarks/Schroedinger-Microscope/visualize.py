import matplotlib.pyplot as plt

def add_to_axes(ax_zs, ax_psps, zs, psps, params, additional_info):
    xmin,xmax,ymin,ymax = params['xmin'],params['xmax'],params['ymin'],params['ymax']
    num_post_selections = params['num_post_selections']
    num_pixels = params['num_pixels']
    shots = params['shots']
    vendor = additional_info['vendor']
    device = additional_info['device_name']

    ax_psps.imshow(psps, cmap = 'gray', extent = (xmin,xmax,ymin,ymax), vmin = 0, vmax = 1)
    ax_psps.set_title(f'{vendor}:{device} PSP({num_post_selections},{num_pixels},{shots})')
    ax_psps.set_xlabel('Re(z)')
    ax_psps.set_ylabel('Im(z)')

    ax_zs.imshow(zs, cmap = 'gray', extent = (xmin,xmax,ymin,ymax), vmin = 0, vmax = 1)
    ax_zs.set_title(f'{vendor}:{device} SP({num_post_selections},{num_pixels},{shots})')
    ax_zs.set_xlabel('Re(z)')
    ax_zs.set_ylabel('Im(z)')

def default_visualize(collated_result, additional_info):
    fig = plt.figure(figsize = (12,6))
    ax_psps = fig.add_subplot(1,2,1)
    ax_zs = fig.add_subplot(1,2,2)
    zs, psps, params = collated_result
    add_to_axes(ax_zs, ax_psps, zs, psps, params, additional_info)
    return fig
