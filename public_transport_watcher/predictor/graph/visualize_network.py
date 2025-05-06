import matplotlib.pyplot as plt
import networkx as nx


def visualize_network(G, node_size=50, with_labels=False):
    """
    Visualize the transport network using geographical coordinates

    Parameters:
    -----------
    G : networkx.DiGraph
        The transport network graph
    node_size : int
        Size of nodes in visualization
    with_labels : bool
        Whether to show station labels
    """
    pos = nx.get_node_attributes(G, "pos")

    plt.figure(figsize=(12, 10))

    nx.draw_networkx(
        G,
        pos=pos,
        with_labels=with_labels,
        node_size=node_size,
        node_color="blue",
        edge_color="gray",
        arrows=True,
        arrowsize=10,
        width=1.0,
        font_size=8,
    )

    plt.title("Transport Network")
    plt.axis("off")
    plt.tight_layout()
    plt.show()
