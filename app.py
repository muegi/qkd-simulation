"""
BB84 Quantum Key Distribution Protocol Simulation
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import plotly.graph_objects as go

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from bb84_protocol import BB84Protocol
from noise_models import NoiseModel
from eavesdropper import Eavesdropper
from metrics import BB84Metrics

# Page configuration
st.set_page_config(
    page_title="BB84 QKD Simulation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal professional styling
st.markdown("""
    <style>
    h1 {
        font-family: 'monospace', serif;
        padding-bottom: 10px;
    }
    
    h2, h3 {
        font-family: 'monospace', serif;
        margin-top: 30px;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: bold;
    }
    
    .dataframe {
        font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Quantum Key Distribution Simulation of the BB84 Protocol Over A Noisy and Lossy Channel")

st.markdown("---")

def create_interactive_bloch_sphere(state_vector, title="Quantum State", show_values=True):
    """
    Create an interactive 3D Bloch sphere using Plotly.
    
    Args:
        state_vector: Qiskit Statevector object
        title: Title for the plot
        show_values: Whether to show x, y, z values
        
    Returns:
        plotly figure and Bloch vector components
    """
    # Calculate Bloch vector components
    alpha = state_vector[0]
    beta = state_vector[1]
    
    # Bloch vector (magnitude = 1 for pure states)
    x_bloch = float(2 * np.real(np.conj(alpha) * beta))
    y_bloch = float(2 * np.imag(np.conj(alpha) * beta))
    z_bloch = float(np.abs(alpha)**2 - np.abs(beta)**2)
    
    # Create figure
    fig = go.Figure()
    
    # Add Bloch vector arrow (red)
    fig.add_trace(
        go.Scatter3d(
            x=[0, x_bloch], 
            y=[0, y_bloch], 
            z=[0, z_bloch], 
            mode='lines+markers',
            marker=dict(size=10, color='red'),
            line=dict(width=5, color='red'),
            name="Bloch Vector",
            showlegend=False
        )
    )
    
    # Create unit sphere (radius = 1, mathematically correct)
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    radius = 1.0  # Unit sphere (mathematical standard)
    x_sphere = radius * np.outer(np.cos(u), np.sin(v))
    y_sphere = radius * np.outer(np.sin(u), np.sin(v))
    z_sphere = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    
    fig.add_trace(
        go.Surface(
            x=x_sphere, 
            y=y_sphere, 
            z=z_sphere,
            colorscale='Oranges',
            opacity=0.5,
            showscale=False,
            hoverinfo='skip'
        )
    )
    
    # Add coordinate axes (extend slightly beyond unit sphere)
    axis_length = 1.2  # Extends 20% beyond unit sphere
    
    # X axis
    fig.add_trace(go.Scatter3d(
        x=[-axis_length, axis_length], y=[0, 0], z=[0, 0],
        mode='lines', line=dict(color='#888888', width=2),
        showlegend=False, hoverinfo='skip'
    ))
    
    # Y axis
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[-axis_length, axis_length], z=[0, 0],
        mode='lines', line=dict(color='#888888', width=2),
        showlegend=False, hoverinfo='skip'
    ))
    
    # Z axis
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[-axis_length, axis_length],
        mode='lines', line=dict(color='#888888', width=2),
        showlegend=False, hoverinfo='skip'
    ))
    
    # Add axis labels (positioned just outside axes)
    label_offset = 0.15
    
    fig.add_trace(go.Scatter3d(
        x=[axis_length + label_offset], y=[0], z=[0],
        mode='text', text=['X'], textfont=dict(size=16, color='#777777'),
        showlegend=False, hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[0], y=[axis_length + label_offset], z=[0],
        mode='text', text=['Y'], textfont=dict(size=16, color='#777777'),
        showlegend=False, hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[axis_length + label_offset],
        mode='text', text=['|0⟩'], textfont=dict(size=16, color='#777777'),
        showlegend=False, hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[-axis_length - label_offset],
        mode='text', text=['|1⟩'], textfont=dict(size=16, color='#777777'),
        showlegend=False, hoverinfo='skip'
    ))
    
    # Layout - mathematically correct range
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(
                showgrid=True,
                gridwidth=1,  # Adjust grid thickness (0.5-1.5)
                showticklabels=True,
                tickfont=dict(size=12),  # Adjust numbers size (9-14)
                title='X',
                range=[-1.5, 1.5]  # Mathematically correct for unit sphere
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,  # Adjust grid thickness
                showticklabels=True,
                tickfont=dict(size=12),  # Adjust numbers size
                title='Y',
                range=[-1.5, 1.5]  # Mathematically correct for unit sphere
            ),
            zaxis=dict(
                showgrid=True,
                gridwidth=1,  # Adjust grid thickness
                showticklabels=True,
                tickfont=dict(size=12),  # Adjust numbers size
                title='Z',
                range=[-1.5, 1.5]  # Mathematically correct for unit sphere
            ),
            aspectmode='cube',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
        ),
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=450
    )
    
    return fig, (x_bloch, y_bloch, z_bloch)


# Sidebar configuration
st.sidebar.header("Simulation Parameters")

st.sidebar.markdown("### Protocol Configuration")

n_qubits = st.sidebar.slider(
    "Number of Qubits",
    min_value=100,
    max_value=10000,
    value=1000,
    step=100,
    help="Total number of qubits transmitted by Alice"
)

st.sidebar.markdown("### Channel Noise Model")

depolarization_prob = st.sidebar.slider(
    "Depolarization Probability",
    min_value=0.00,
    max_value=1.00,
    value=0.00,
    step=0.01,
    format="%.2f",
    help="Probability of X, Y, or Z gate error"
)

photon_loss_prob = st.sidebar.slider(
    "Photon Loss Probability",
    min_value=0.00,
    max_value=1.00,
    value=0.00,
    step=0.01,
    format="%.2f",
    help="Probability of photon loss during transmission"
)

st.sidebar.markdown("### Security Analysis")

eve_enabled = st.sidebar.checkbox(
    "Enable Eavesdropper",
    value=False,
    help="Simulate intercept-resend attack"
)

st.sidebar.markdown("---")
run_button = st.sidebar.button("Run Simulation", type="primary", use_container_width=True)

# Main simulation execution
if run_button:
    
    # Progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Initializing BB84 protocol...")
    progress_bar.progress(10)
    bb84 = BB84Protocol(n_qubits=n_qubits)
    
    status_text.text("Alice preparing quantum states...")
    progress_bar.progress(20)
    qubits = bb84.alice_prepare_qubits()
    
    status_text.text("Simulating quantum channel noise...")
    progress_bar.progress(40)
    noise = NoiseModel(
        depolarization_prob=depolarization_prob,
        photon_loss_prob=photon_loss_prob
    )
    noisy_qubits, lost_indices = noise.apply_noise_to_channel(qubits)
    
    status_text.text("Checking for eavesdropping...")
    progress_bar.progress(60)
    eve = Eavesdropper(enabled=eve_enabled)
    intercepted_qubits = eve.intercept_and_resend(noisy_qubits)
    
    status_text.text("Bob measuring qubits...")
    progress_bar.progress(80)
    alice_bits_after_loss = np.delete(bb84.alice_bits, lost_indices)
    alice_bases_after_loss = np.delete(bb84.alice_bases, lost_indices)
    bb84.bob_measure_qubits(intercepted_qubits)
    bb84.alice_bits = alice_bits_after_loss
    bb84.alice_bases = alice_bases_after_loss
    bb84.sift_keys()
    
    status_text.text("Calculating metrics...")
    progress_bar.progress(90)
    metrics = BB84Metrics()
    results = metrics.calculate_all_metrics(
        initial_qubits=n_qubits,
        lost_qubits=len(lost_indices),
        alice_key=bb84.sifted_key_alice,
        bob_key=bb84.sifted_key_bob
    )
    
    progress_bar.progress(100)
    status_text.text("Complete")
    progress_bar.empty()
    status_text.empty()
    
    # Results
    st.markdown("---")
    st.header("Simulation Results")
    
    # KPIs
    st.subheader("1. Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Quantum Bit Error Rate", f"{results['qber']:.2f}%")
    
    with col2:
        st.metric("Final Key Length", f"{results['final_key_length']} bits")
    
    with col3:
        st.metric("Key Generation Rate", f"{results['key_generation_rate']:.4f}")
    
    with col4:
        st.metric("Photon Loss Rate", f"{(results['lost_qubits']/results['initial_qubits']*100):.2f}%")
    
    # Detailed stats tables
    st.subheader("2. Detailed Protocol Statistics")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("**Transmission Phase**")
        transmission_df = pd.DataFrame({
            "Parameter": [
                "Initial Qubits Transmitted",
                "Qubits Lost in Channel",
                "Qubits Successfully Received",
                "Channel Transmission Efficiency"
            ],
            "Value": [
                results['initial_qubits'],
                results['lost_qubits'],
                results['received_qubits'],
                f"{(results['received_qubits']/results['initial_qubits']*100):.2f}%"
            ]
        })
        st.dataframe(transmission_df, hide_index=True, use_container_width=True)
    
    with col_right:
        st.markdown("**Key Generation Phase**")
        key_gen_df = pd.DataFrame({
            "Parameter": [
                "Sifted Key Length",
                "Bits Sampled for Error Detection",
                "Errors Detected in Sample",
                "Final Secure Key Length"
            ],
            "Value": [
                results['sifted_key_length'],
                results['sampled_bits'],
                results['error_count'],
                results['final_key_length']
            ]
        })
        st.dataframe(key_gen_df, hide_index=True, use_container_width=True)
    
    # Security analysis
    st.subheader("3. Security Analysis")
    
    if eve_enabled:
        security_df = pd.DataFrame({
            "Security Metric": [
                "Eavesdropper Status",
                "Qubits Intercepted",
                "QBER Level",
                "Expected QBER (Intercept-Resend)",
                "Security Assessment"
            ],
            "Value": [
                "ACTIVE",
                eve.intercepted_count,
                f"{results['qber']:.2f}%",
                "~25%",
                "COMPROMISED" if results['qber'] > 11 else "SECURE"
            ]
        })
        st.dataframe(security_df, hide_index=True, use_container_width=True)
    else:
        st.markdown(f"""
        **Channel Security Assessment:**
        - No eavesdropping simulated
        - QBER: {results['qber']:.2f}%
        - Security threshold: 11%
        - Status: **{'SECURE' if results['qber'] < 11 else 'INSECURE'}**
        """)
    
    # Visualizations
    st.markdown("---")
    st.header("Data Visualization and Analysis")
    
    # Bloch Sphere Visualization - Before and After
    st.subheader("4. Quantum State Visualization (Bloch Spheres)")
    
    col_before, col_after = st.columns(2)
    
    # Before transmission (Alice's prepared state)
    with col_before:
        st.markdown("**Before Transmission (Alice's Prepared State)**")
        
        if len(qubits) > 0:
            # Select a random qubit to display
            sample_idx = np.random.randint(0, len(qubits))
            qc_before = qubits[sample_idx]
            state_before = Statevector.from_instruction(qc_before)
            
            # Get original basis and bit
            basis_before = bb84.alice_bases[:len(qubits)][sample_idx] if sample_idx < len(bb84.alice_bases[:len(qubits)]) else 0
            bit_before = bb84.alice_bits[:len(qubits)][sample_idx] if sample_idx < len(bb84.alice_bits[:len(qubits)]) else 0
            basis_label_before = "Rectilinear" if basis_before == 0 else "Diagonal"
            
            bloch_fig_before, (x_b, y_b, z_b) = create_interactive_bloch_sphere(
                state_before, 
                f"Alice's State: {basis_label_before} |{bit_before}⟩"
            )
            st.plotly_chart(bloch_fig_before, use_container_width=True, key="bloch_before")
            
            # Display Bloch vector values
            bloch_values_before = pd.DataFrame({
                "Component": ["X", "Y", "Z"],
                "Value": [f"{x_b:.4f}", f"{y_b:.4f}", f"{z_b:.4f}"]
            })
            st.dataframe(bloch_values_before, hide_index=True, use_container_width=True)
    
    # After transmission (with noise/Eve)
    with col_after:
        st.markdown("**After Transmission (With Noise/Eve)**")
        
        if len(noisy_qubits) > 0:
            # Select a random qubit from the noisy channel
            sample_idx_after = np.random.randint(0, len(noisy_qubits))
            qc_after = noisy_qubits[sample_idx_after]
            state_after = Statevector.from_instruction(qc_after)
            
            # Get basis and bit for this qubit
            if sample_idx_after < len(alice_bases_after_loss):
                basis_after = alice_bases_after_loss[sample_idx_after]
                bit_after = alice_bits_after_loss[sample_idx_after]
                basis_label_after = "Rectilinear" if basis_after == 0 else "Diagonal"
                
                bloch_fig_after, (x_a, y_a, z_a) = create_interactive_bloch_sphere(
                    state_after, 
                    f"After Channel: {basis_label_after} |{bit_after}⟩"
                )
                st.plotly_chart(bloch_fig_after, use_container_width=True, key="bloch_after")
                
                # Display Bloch vector values
                bloch_values_after = pd.DataFrame({
                    "Component": ["X", "Y", "Z"],
                    "Value": [f"{x_a:.4f}", f"{y_a:.4f}", f"{z_a:.4f}"]
                })
                st.dataframe(bloch_values_after, hide_index=True, use_container_width=True)
    
    # Key generation flow
    st.subheader("5. Key Generation Pipeline")
    
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    
    stages = ['Initial\nQubits', 'After\nChannel Loss', 'After\nSifting', 'After Error\nDetection', 'Final\nKey']
    values = [
        results['initial_qubits'],
        results['received_qubits'],
        results['sifted_key_length'],
        results['sifted_key_length'] - results['sampled_bits'],
        results['final_key_length']
    ]
    
    colors = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE']
    bars = ax1.bar(stages, values, color=colors, edgecolor='black', linewidth=1.5)
    
    ax1.set_ylabel('Number of Bits', fontsize=12, fontweight='bold')
    ax1.set_title('BB84 Protocol: Key Generation Pipeline', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(value)}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    st.pyplot(fig1)
    plt.close()
    
    # Basis distribution
    st.subheader("6. Basis Selection Distribution")
    
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(12, 5))
    
    alice_rectilinear = np.sum(alice_bases_after_loss == 0)
    alice_diagonal = np.sum(alice_bases_after_loss == 1)
    
    ax2a.pie([alice_rectilinear, alice_diagonal], 
             labels=['Rectilinear (|0⟩, |1⟩)', 'Diagonal (|+⟩, |−⟩)'],
             autopct='%1.1f%%',
             colors=['#1E3A8A', '#3B82F6'],
             startangle=90)
    ax2a.set_title("Alice's Basis Selection", fontweight='bold')
    
    bob_rectilinear = np.sum(bb84.bob_bases == 0)
    bob_diagonal = np.sum(bb84.bob_bases == 1)
    
    ax2b.pie([bob_rectilinear, bob_diagonal],
             labels=['Rectilinear', 'Diagonal'],
             autopct='%1.1f%%',
             colors=['#1E3A8A', '#3B82F6'],
             startangle=90)
    ax2b.set_title("Bob's Basis Selection", fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()
    
    # Error visualization
    if results['sifted_key_length'] > 0:
        st.subheader("7. Key Bit Comparison")
        
        fig3, ax3 = plt.subplots(figsize=(12, 4))
        
        display_bits = min(100, results['sifted_key_length'])
        x_pos = np.arange(display_bits)
        
        alice_bits_display = bb84.sifted_key_alice[:display_bits]
        bob_bits_display = bb84.sifted_key_bob[:display_bits]
        errors_display = alice_bits_display != bob_bits_display
        
        # Plot Alice's bits
        ax3.scatter(
            x_pos[alice_bits_display == 0], 
            np.zeros(np.sum(alice_bits_display == 0)), 
            marker='o', s=50, c='#1E3A8A', label='Alice |0⟩', alpha=0.7
        )
        ax3.scatter(
            x_pos[alice_bits_display == 1], 
            np.zeros(np.sum(alice_bits_display == 1)), 
            marker='s', s=50, c='#3B82F6', label='Alice |1⟩', alpha=0.7
        )
        
        # Plot Bob's bits
        ax3.scatter(
            x_pos[bob_bits_display == 0], 
            np.ones(np.sum(bob_bits_display == 0)), 
            marker='o', s=50, c='#1E3A8A', label='Bob |0⟩', alpha=0.7
        )
        ax3.scatter(
            x_pos[bob_bits_display == 1], 
            np.ones(np.sum(bob_bits_display == 1)), 
            marker='s', s=50, c='#3B82F6', label='Alice |1⟩', alpha=0.7
        )
        
        # Highlight errors
        if np.any(errors_display):
            error_positions = x_pos[errors_display]
            for pos in error_positions:
                ax3.axvline(x=pos, color='red', alpha=0.3, linestyle='--', linewidth=2)
        
        ax3.set_ylim(-0.5, 1.5)
        ax3.set_yticks([0, 1])
        ax3.set_yticklabels(['Alice', 'Bob'])
        ax3.set_xlabel('Bit Position in Sifted Key', fontweight='bold')
        ax3.set_title(f'Sifted Key Comparison (First {display_bits} bits)', fontweight='bold')
        ax3.legend(loc='upper right', ncol=4)
        ax3.grid(axis='x', alpha=0.3)
        
        st.pyplot(fig3)
        plt.close()
        
        st.caption(f"Red dashed lines indicate bit errors. Total errors in sample: {results['error_count']}/{results['sampled_bits']}")
    
    # QBER analysis
    st.subheader("8. Quantum Bit Error Rate Analysis")
    
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    
    qber_categories = ['No Eve\n(Noise Only)', 'Eve Present\n(Intercept-Resend)', 
                      'Security\nThreshold', 'Current\nQBER']
    qber_values = [
        depolarization_prob * 100 / 3 if depolarization_prob > 0 else 0,
        25.0,
        11.0,
        results['qber']
    ]
    
    colors_qber = ['#10B981', '#EF4444', '#F59E0B', '#1E3A8A']
    bars = ax4.barh(qber_categories, qber_values, color=colors_qber, edgecolor='black', linewidth=1.5)
    
    ax4.set_xlabel('QBER (%)', fontsize=12, fontweight='bold')
    ax4.set_title('QBER Comparison and Security Analysis', fontsize=14, fontweight='bold')
    ax4.axvline(x=11, color='red', linestyle='--', linewidth=2, label='Security Threshold (11%)')
    ax4.legend()
    ax4.grid(axis='x', alpha=0.3)
    
    for bar, value in zip(bars, qber_values):
        width = bar.get_width()
        ax4.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                f'{value:.2f}%',
                ha='left', va='center', fontweight='bold', fontsize=10)
    
    st.pyplot(fig4)
    plt.close()
    
    # Key samples
    st.subheader("9. Generated Key Samples")
    
    col_alice_key, col_bob_key = st.columns(2)
    
    with col_alice_key:
        st.markdown("**Alice's Sifted Key (first 50 bits):**")
        if len(bb84.sifted_key_alice) > 0:
            sample_alice = ''.join(map(str, bb84.sifted_key_alice[:50]))
            st.code(sample_alice, language=None)
        else:
            st.warning("No key generated")
    
    with col_bob_key:
        st.markdown("**Bob's Sifted Key (first 50 bits):**")
        if len(bb84.sifted_key_bob) > 0:
            sample_bob = ''.join(map(str, bb84.sifted_key_bob[:50]))
            st.code(sample_bob, language=None)
        else:
            st.warning("No key generated")
    
    # Conclusion
    st.markdown("---")
    st.header("Conclusion")
    
    if results['qber'] < 5:
        st.success(f"**Result: Secure Communication Established**\n\nQBER of {results['qber']:.2f}% is well below the security threshold. The channel is suitable for secure key distribution.")
    elif results['qber'] < 11:
        st.warning(f"**Result: Moderate Noise Detected**\n\nQBER of {results['qber']:.2f}% is elevated but below the critical threshold. Error correction protocols may be applied to extract a secure key.")
    else:
        st.error(f"**Result: Communication Compromised**\n\nQBER of {results['qber']:.2f}% exceeds the security threshold of 11%. {'Eavesdropping detected.' if eve_enabled else 'Excessive channel noise detected.'} Protocol should be aborted.")

else:
    # Initial state
    st.header("Description")
    
    st.markdown("""
    
    This project is a simulation of the BB84 protocol over a noisy and lossy channel built with Python, Qiskit, and Streamlit. It attempts to model more realistic conditions using Qiskit to model quantum states and by applying configurable noise operators and an eavesdropper with an intercept-resend attack where their parameters can be adjusted to visualise and analyse their effects on QBER, key generation rate, final key length, and overall protocol security.""")
    
    st.markdown("""
    ### BB84 Protocol
    
    future alyssa: explain the protocol here
    
    #### Protocol Steps:
    
    1. **Qubit Preparation**: Alice encodes random classical bits using randomly selected bases
    2. **Quantum Transmission**: Qubits are transmitted through a quantum channel
    3. **Measurement**: Bob measures received qubits using randomly selected bases
    4. **Basis Reconciliation**: Alice and Bob compare bases and retain matching measurements
    5. **Error Detection**: A subset is compared to estimate QBER
    6. **Privacy Amplification**: Sampled bits are discarded to produce the final secure key
    
    #### Security Principles:
    
    - **No-Cloning Theorem**: Quantum states cannot be perfectly copied
    - **Measurement Disturbance**: Eavesdropping introduces detectable errors
    
    #### Noise Models:
    
    - **Depolarization**: Random Pauli gates simulating decoherence
    - **Photon Loss**: Random qubit loss simulating attenuation
    - **Eavesdropping**: Intercept-resend attack
    """)

# Footer
st.markdown("---")
st.caption("hi tom :] this is alyssa writing from python at 3:28 AM currently dazed out of my mind, what should i put here or alternatively is a footer even needed? also, how is the UI in general? p.s hi alyssa from the future, you still need to get shrimp")