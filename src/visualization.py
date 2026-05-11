"""
Visualization utilities for BB84 simulation
"""

import matplotlib.pyplot as plt
import numpy as np
from qiskit.visualization import plot_bloch_multivector
from qiskit.quantum_info import Statevector


class BB84Visualizer:
    """
    Visualization tools for BB84 protocol.
    """
    
    def __init__(self):
        """Initialize visualizer."""
        pass
    
    def plot_qber_vs_noise(self, noise_range, qber_values, noise_type="depolarization"):
        """
        Plot QBER as a function of noise parameter.
        
        Args:
            noise_range (list): Range of noise probabilities
            qber_values (list): Corresponding QBER values
            noise_type (str): Type of noise ("depolarization" or "photon_loss")
        
        Returns:
            matplotlib.figure.Figure: The plot figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(noise_range, qber_values, 'b-', linewidth=2, marker='o', markersize=6)
        ax.set_xlabel(f'{noise_type.capitalize()} Probability', fontsize=12)
        ax.set_ylabel('QBER (%)', fontsize=12)
        ax.set_title(f'QBER vs {noise_type.capitalize()}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def plot_key_length_vs_noise(self, noise_range, key_lengths_no_eve, key_lengths_with_eve=None):
        """
        Plot final key length as a function of noise.
        
        Args:
            noise_range (list): Range of noise probabilities
            key_lengths_no_eve (list): Key lengths without Eve
            key_lengths_with_eve (list, optional): Key lengths with Eve
        
        Returns:
            matplotlib.figure.Figure: The plot figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(noise_range, key_lengths_no_eve, 'g-', linewidth=2, marker='s', 
                markersize=6, label='Without Eve')
        
        if key_lengths_with_eve:
            ax.plot(noise_range, key_lengths_with_eve, 'r-', linewidth=2, marker='^',
                    markersize=6, label='With Eve')
        
        ax.set_xlabel('Noise Probability', fontsize=12)
        ax.set_ylabel('Final Key Length (bits)', fontsize=12)
        ax.set_title('Key Length vs Noise', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig


# Test
if __name__ == "__main__":
    print("Visualization module loaded successfully!")
    print("Use this module to create plots for your simulation results.")