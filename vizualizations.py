import imageio

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, roc_auc_score


def plot_confusion_matrix(y_true, y_pred, labels, title=None, img_file=None):

    font = {'size'   : 25}
    plt.rc('font', **font)
    
    cm = confusion_matrix(y_true, y_pred, labels=labels, normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap=plt.cm.Blues)
    disp.im_.colorbar.remove()
    
    fig = disp.figure_
    plt.xticks(rotation=90)
    
    fig.set_figwidth(18)
    fig.set_figheight(18)
    
    for labels in disp.text_.ravel():
        labels.set_fontsize(10)
    
    if title:
        disp.ax_.set_title(title)
    
    plt.tight_layout()

    if img_file:
        plt.savefig(img_file)

def plot_roc_curves(y_true, y_pred, labels, title=None, img_file=None):

    chance = np.arange(0,1,0.01)
    plt.figure(figsize=(12,14))
    plt.plot(chance, chance, '--', color='black', label='Random Chance (AUC = 0.5)')

    for i, label in enumerate(labels):

        score = roc_auc_score(y_true[:, i], y_pred[:, i])
        fpr, tpr, _ = roc_curve(y_true[:, i], y_pred[:, i])
        plt.plot(fpr, tpr, label=f"{label} (AUC = {score:.2f})")

    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.3), fancybox=True, shadow=False, ncol=3, fontsize = 14)
    plt.title(title)
    plt.tight_layout()
    plt.gca().set_aspect('equal')

    if img_file:
        plt.savefig(img_file)


def make_gif(files, gif_file=None):

    # Load the images
    images = []
    for filename in files:
        images.append(imageio.imread(filename))

    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(18, 18))

    # Create the animation
    def animate(i):
        ax.clear()
        ax.axis('off')
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
        ax.imshow(images[i])
        
    anim = animation.FuncAnimation(fig, animate, frames=len(images), interval=500)

    if gif_file:
        # Save the animation as a GIF
        anim.save(gif_file)

