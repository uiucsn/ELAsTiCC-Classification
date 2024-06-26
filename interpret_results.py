import os
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from networkx.drawing.nx_agraph import write_dot, graphviz_layout
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report

from taxonomy import source_node_label
from vizualizations import plot_confusion_matrix, plot_roc_curves

def get_indices_where(arr, target):
    
    to_return = []
    for i, obs in enumerate(arr):
        if obs == target:
            to_return.append(i)
            
    return to_return

def get_conditional_probabilites(y_pred, tree):
    
    # Create a new arrays to store pseudo (conditional) probabilities.
    pseudo_conditional_probabilities = np.copy(y_pred)
    pseudo_probabilities = np.copy(y_pred)

    level_order_nodes = list(nx.bfs_tree(tree, source=source_node_label).nodes())
    parents = [list(tree.predecessors(node)) for node in level_order_nodes]
    for idx in range(len(parents)):

        # Make sure the graph is a tree.
        assert len(parents[idx]) == 0 or len(parents[idx]) == 1, 'Number of parents for each node should be 0 (for root) or 1.'
        
        if len(parents[idx]) == 0:
            parents[idx] = ''
        else:
            parents[idx] = parents[idx][0]

    # Finding unique parents for masking
    unique_parents = list(set(parents))
    unique_parents.sort()

    # Create masks for applying soft max and calculating loss values.
    masks = []
    for parent in unique_parents:
        masks.append(get_indices_where(parents, parent))
    
    # Get the masked softmaxes
    for mask in masks:
        pseudo_probabilities[:, mask] = np.exp(y_pred[:, mask]) / np.sum(np.exp(y_pred[:, mask]), axis=1, keepdims=True)
        

    for node in level_order_nodes:
        
        # Find path from node to 
        path = list(nx.shortest_path(tree, source_node_label, node))
        
        # Get the index of the node for which we are calculating the pseudo probability
        node_index = level_order_nodes.index(node)
        
        # Indices of all the classes in the path from source to the node for which we are calculating the pseudo probability
        path_indices = [level_order_nodes.index(u) for u in path]
        
        #print(node, path, node_index, path_indices, pseudo_probabilities[:, path_indices])
        
        # Multiply the pseudo probabilites of all the classes in the path so that we get the conditional pseudo probabilites
        pseudo_conditional_probabilities[:, node_index] = np.prod(pseudo_probabilities[:, path_indices], axis = 1)
        
    return pseudo_probabilities, pseudo_conditional_probabilities

def save_leaf_cf_and_rocs(y_true, y_pred, tree, model_dir, fraction="NA"):
    
    # Find the indexes of the leaf nodes i.e. nodes with out degree = 0.
    level_order_nodes = list(nx.bfs_tree(tree, source=source_node_label).nodes())
    n_children = [tree.out_degree(node) for node in level_order_nodes]
    idx = get_indices_where(n_children, 0)

    leaf_labels = np.array(level_order_nodes)[idx]
    
    y_pred_label = [leaf_labels[i] for i in np.argmax(y_pred[:, idx], axis=1)]
    y_true_label = [leaf_labels[i] for i in np.argmax(y_true[:, idx], axis=1)]

    # Make plots
    plot_title = f"~{fraction * 100}% of each LC visible"

    # Make the dirs to store results
    os.makedirs(f"{model_dir}/gif/leaf_cf", exist_ok=True)
    os.makedirs(f"{model_dir}/gif/leaf_roc", exist_ok=True)
    os.makedirs(f"{model_dir}/gif/leaf_csv", exist_ok=True)

    cf_plot_file = f"{model_dir}/gif/leaf_cf/{fraction}.png"
    roc_plot_file = f"{model_dir}/gif/leaf_roc/{fraction}.png"
    csv_plot_file = f"{model_dir}/gif/leaf_csv/{fraction}.csv"
    
    plot_confusion_matrix(y_true_label, y_pred_label, leaf_labels, plot_title, cf_plot_file)
    plt.close()
    
    plot_roc_curves(y_true[:, idx], y_pred[:, idx], leaf_labels, plot_title, roc_plot_file)
    plt.close()

    report = classification_report(y_true_label, y_pred_label)
    print(report)
    report = classification_report(y_true_label, y_pred_label, output_dict=True)
    pd.DataFrame(report).transpose().to_csv(csv_plot_file)
    print('===========')

def save_all_cf_and_rocs(y_true, y_pred, tree, model_dir, fraction="NA"):
    
    def get_path_length(tree, source, target):
        return len(nx.shortest_path(tree, source=source, target=target)) - 1
    
    # Find the parents
    level_order_nodes = list(nx.bfs_tree(tree, source=source_node_label).nodes())
    depths = [get_path_length(tree, source_node_label, node) for node in level_order_nodes]
    
    # Finding unique depths for masking
    unique_depths = list(set(depths))
    unique_depths.sort()

    # Create masks for classification
    masks = []
    for depth in unique_depths:
        masks.append(get_indices_where(depths, depth))
    
    # Get the masked softmaxes
    for mask, depth in zip(masks, unique_depths):
        
        # Every alert 
        if depth != 0 and depth != 3:
        
            true_labels = []
            pred_labels = []
            
            mask_classes = [level_order_nodes[m] for m in mask]
            for i in range(y_true.shape[0]):

                # Find the true label
                true_class_idx = np.argmax(y_true[i, mask])
                true_labels.append(mask_classes[true_class_idx])

                # Find the predicted label
                predicted_class_idx = np.argmax(y_pred[i, mask])
                pred_labels.append(mask_classes[predicted_class_idx])
            
            plot_title = f"~{fraction * 100}% of each LC visible"

            # Create the dirs to save plots
            os.makedirs(f"{model_dir}/gif/level_{depth}_cf", exist_ok=True)
            os.makedirs(f"{model_dir}/gif/level_{depth}_roc", exist_ok=True)
            os.makedirs(f"{model_dir}/gif/level_{depth}_csv", exist_ok=True)

            cf_plot_file = f"{model_dir}/gif/level_{depth}_cf/{fraction}.png"
            roc_plot_file = f"{model_dir}/gif/level_{depth}_roc/{fraction}.png"
            csv_plot_file = f"{model_dir}/gif/level_{depth}_csv/{fraction}.csv"

            plot_confusion_matrix(true_labels, pred_labels, mask_classes, plot_title, cf_plot_file)
            plt.close()

            plot_roc_curves(y_true[:, mask], y_pred[:, mask], mask_classes, plot_title, roc_plot_file)
            plt.close()
            
            report = classification_report(true_labels, pred_labels)
            print(report)
            report = classification_report(true_labels, pred_labels, output_dict=True)
            pd.DataFrame(report).transpose().to_csv(csv_plot_file)
            print('===========')