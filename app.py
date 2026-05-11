"""
BB84 Quantum Key Distribution Protocol Simulation
"""

import streamlit as st
import numpy as np
import pandas as pd
import sys
from pathlib import Path
from qiskit.quantum_info import Statevector
import plotly.graph_objects as go
import plotly.express as px


# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.bb84_protocol import BB84Protocol
from src.noise_models import NoiseModel
from src.eavesdropper import Eavesdropper
from src.error_correction import CASCADEErrorCorrection
from src.privacy_amplification import PrivacyAmplification


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
            x=[0, x_bloch * 0.91], 
            y=[0, y_bloch * 0.91], 
            z=[0, z_bloch * 0.91], 
            mode='lines+markers',
            marker=dict(size=8, color='red'),
            line=dict(width=8, color='red'),
            name="Bloch Vector",
            showlegend=False
        )
    )
    
    # Create unit sphere
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    radius = 1.0
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
    
    axis_length = 1.2  
    
    # X axis
    fig.add_trace(go.Scatter3d(
        x=[-axis_length, axis_length], y=[0, 0], z=[0, 0],
        mode='lines', line=dict(width=2),
        showlegend=False, hoverinfo='skip'
    ))
    
    # Y axis
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[-axis_length, axis_length], z=[0, 0],
        mode='lines', line=dict(width=2),
        showlegend=False, hoverinfo='skip'
    ))
    
    # Z axis
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[-axis_length, axis_length],
        mode='lines', line=dict(width=2),
        showlegend=False, hoverinfo='skip'
    ))
    
# Add axis labels (positioned just outside axes)
    label_offset = 0.15
    
    # Z-axis labels (Computational/Rectilinear basis)
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[axis_length + label_offset],
        mode='text', text=['|0⟩'], textfont=dict(size=16),
        showlegend=False, hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[-axis_length - label_offset - 0.15],
        mode='text', text=['|1⟩'], textfont=dict(size=16),
        showlegend=False, hoverinfo='skip'
    ))
    
    # X-axis labels (Diagonal/Hadamard basis)
    fig.add_trace(go.Scatter3d(
        x=[axis_length + label_offset], y=[0], z=[0],
        mode='text', text=['|+⟩'], textfont=dict(size=16),
        showlegend=False, hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[-axis_length - label_offset], y=[0], z=[0],
        mode='text', text=['|−⟩'], textfont=dict(size=16),
        showlegend=False, hoverinfo='skip'
    ))
    

    
    # Bloch Sphere Layout Configuration
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                showticklabels=True,
                tickfont=dict(size=12),
                title='X',
                range=[-1.5, 1.5]
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                showticklabels=True,
                tickfont=dict(size=12),
                title='Y',
                range=[-1.5, 1.5]
            ),
            zaxis=dict(
                showgrid=True,
                gridwidth=1,
                showticklabels=True,
                tickfont=dict(size=12),
                title='Z',
                range=[-1.5, 1.5]
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

# Reset counter approach
if 'reset_count' not in st.session_state:
    st.session_state.reset_count = 0

# Default values
default_qubits = 100
default_depol = 0.00
default_loss = 0.00
default_eve = False

# Protocol Configuration
st.sidebar.markdown("### Protocol Configuration")

n_qubits = st.sidebar.slider(
    "Number of Qubits",
    min_value=100,
    max_value=10000,
    value=default_qubits,
    step=100,
    help="Total number of qubits transmitted by Alice",
    key=f'n_qubits_{st.session_state.reset_count}'  # Unique key per reset
)

# Quantum Channel Model
st.sidebar.markdown("### Channel Parameters")

depolarization_prob = st.sidebar.slider(
    "Depolarization Probability",
    min_value=0.00,
    max_value=1.00,
    value=default_depol,
    step=0.01,
    format="%.2f",
    help="Probability of X, Y, or Z gate error",
    key=f'depol_{st.session_state.reset_count}'
)

photon_loss_prob = st.sidebar.slider(
    "Photon Loss Probability",
    min_value=0.00,
    max_value=1.00,
    value=default_loss,
    step=0.01,
    format="%.2f",
    help="Probability of photon loss during transmission",
    key=f'loss_{st.session_state.reset_count}'
)

# Eavesdropping Simulation
st.sidebar.markdown("### Eavesdropping Simulation")

eve_enabled = st.sidebar.checkbox(
    "Enable Eavesdropper (Eve)",
    value=default_eve,
    help="Simulate intercept-resend attack",
    key=f'eve_{st.session_state.reset_count}'
)

# Action buttons
col_run, col_reset = st.sidebar.columns(2)

with col_run:
    run_button = st.sidebar.button("Run Simulation", type="primary", use_container_width=True)

with col_reset:
    if st.sidebar.button("Reset", use_container_width=True):
        st.session_state.reset_count += 1  # Increment counter
        st.rerun()  # Rerun with new keys

# Main simulation execution
if run_button:
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Initialize protocol
    status_text.text("Initializing BB84 protocol...")
    progress_bar.progress(5)
    bb84 = BB84Protocol(n_qubits=n_qubits)
    
    # Step 2: Alice prepares qubits
    status_text.text("Alice preparing quantum states...")
    progress_bar.progress(10)
    qubits = bb84.alice_prepare_qubits()
    
    # Save original arrays for visualization (before any loss)
    alice_bases_original = bb84.alice_bases.copy()
    alice_bits_original = bb84.alice_bits.copy()
    
    # Step 3: Eavesdropping (before noise)
    status_text.text("Checking for eavesdropping...")
    progress_bar.progress(20)
    eve = Eavesdropper(enabled=eve_enabled)
    intercepted_qubits = eve.intercept_and_resend(qubits)
    
    # Step 4: Channel noise (after Eve)
    status_text.text("Simulating quantum channel noise...")
    progress_bar.progress(30)
    noise = NoiseModel(
        depolarization_prob=depolarization_prob,
        photon_loss_prob=photon_loss_prob
    )
    noisy_qubits, lost_indices = noise.apply_noise_to_channel(intercepted_qubits)
    
    # Step 5: Bob measures qubits
    status_text.text("Bob measuring received qubits...")
    progress_bar.progress(45)
    alice_bits_after_loss = np.delete(bb84.alice_bits, lost_indices)
    alice_bases_after_loss = np.delete(bb84.alice_bases, lost_indices)
    
    bb84.bob_measure_qubits(noisy_qubits)
    bb84.alice_bits = alice_bits_after_loss
    bb84.alice_bases = alice_bases_after_loss
    
    # Step 6: Basis reconciliation (sifting)
    status_text.text("Performing basis reconciliation...")
    progress_bar.progress(55)
    bb84.sift_keys()
    
    # Step 7: Error estimation (sampling)
    status_text.text("Estimating channel error rate (QBER)...")
    progress_bar.progress(65)
    
    sifted_length = len(bb84.sifted_key_alice)
    sample_size = int(sifted_length * 0.15) # Sample 15% of sifted key for error estimation
    
    if sifted_length > 0:
        sample_indices = np.random.choice(sifted_length, sample_size, replace=False)
        
        # Create masks
        sample_mask = np.zeros(sifted_length, dtype=bool)
        sample_mask[sample_indices] = True
        
        # Split into sampled and remaining
        alice_sample = bb84.sifted_key_alice[sample_mask]
        bob_sample = bb84.sifted_key_bob[sample_mask]
        alice_remaining = bb84.sifted_key_alice[~sample_mask]
        bob_remaining = bb84.sifted_key_bob[~sample_mask]
        
        # Calculate QBER from sample
        errors_in_sample = np.sum(alice_sample != bob_sample)
        qber_estimated = (errors_in_sample / sample_size * 100) if sample_size > 0 else 0
    else:
        alice_sample = np.array([])
        bob_sample = np.array([])
        alice_remaining = np.array([])
        bob_remaining = np.array([])
        errors_in_sample = 0
        qber_estimated = 0
        sample_size = 0
    
    # Step 8: Error Correction (CASCADE)
    status_text.text("Performing error correction (CASCADE)...")
    progress_bar.progress(75)
    
    if len(alice_remaining) > 0:
        cascade = CASCADEErrorCorrection()
        bob_corrected, ec_stats = cascade.run_cascade(
            alice_remaining,
            bob_remaining,
            estimated_qber=qber_estimated,
            num_passes=4
        )
    else:
        bob_corrected = np.array([])
        ec_stats = {
            'errors_corrected': 0,
            'bits_disclosed': 0,
            'passes_completed': 0,
            'remaining_errors': 0,
            'correction_success': True
        }
    
    # Step 9: Privacy Amplification
    status_text.text("Applying privacy amplification...")
    progress_bar.progress(85)
    
    if len(bob_corrected) > 0:
        pa = PrivacyAmplification()
        final_key, pa_stats = pa.amplify(
            bob_corrected,
            qber=qber_estimated,
            security_parameter=1e-10,
            seed=42
        )
    else:
        final_key = np.array([])
        pa_stats = {
            'original_length': 0,
            'final_length': 0,
            'compression_ratio': 0.0,
            'bits_removed': 0,
            'binary_entropy': 0.0,
            'security_parameter': 1e-10
        }
    
    # Step 10: Calculate all metrics
    status_text.text("Calculating final metrics...")
    progress_bar.progress(95)
    
    # Store all results
    results = {
        # Transmission metrics
        'initial_qubits': n_qubits,
        'lost_qubits': len(lost_indices),
        'received_qubits': n_qubits - len(lost_indices),
        
        # Sifting metrics
        'sifted_key_length': sifted_length,
        
        # Error estimation metrics
        'sampled_bits': sample_size,
        'error_count': errors_in_sample,
        'qber': qber_estimated,
        
        # Post-sample discard
        'intermediate_key_length': len(alice_remaining),
        
        # Error correction metrics
        'errors_corrected': ec_stats['errors_corrected'],
        'bits_disclosed_ec': ec_stats['bits_disclosed'],
        'cascade_passes': ec_stats['passes_completed'],
        'cascade_success': ec_stats['correction_success'],
        'remaining_errors': ec_stats['remaining_errors'],
        'after_error_correction': len(bob_corrected),
        
        # Privacy amplification metrics
        'binary_entropy': pa_stats['binary_entropy'],
        'compression_ratio': pa_stats['compression_ratio'],
        'bits_removed_pa': pa_stats['bits_removed'],
        'final_key_length': len(final_key),
        
        # Key generation rate (based on final key)
        'key_generation_rate': len(final_key) / n_qubits if n_qubits > 0 else 0,
        
        # Store actual keys for display
        'alice_sample': alice_sample,
        'bob_sample': bob_sample,
        'final_key': final_key
    }
    
    progress_bar.progress(100)
    status_text.text("Simulation complete!")
    progress_bar.empty()
    status_text.empty()
    
    # Results
    st.header("Simulation Results")
    
    # KPIs
    st.subheader("Key Performance Indicators")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Final Key Length", f"{results['final_key_length']} bits")
    
    with col2:
        st.metric("Key Generation Rate", f"{results['key_generation_rate']:.4f}")
    
    with col3:
        st.metric("Quantum Bit Error Rate", f"{results['qber']:.2f}%")


    # Security Analysis Summary

    st.subheader("Security Analysis Summary")
    
    if results['qber'] < 5:
        st.success(
            f"**Secure Communication Established**\n\n"
            f"QBER of {results['qber']:.2f}% is well below the security threshold. "
            f"The channel is suitable for secure key distribution."
        )
    elif results['qber'] < 11:
        st.warning(
            f"**Moderate Noise Detected**\n\n"
            f"QBER of {results['qber']:.2f}% is elevated but below the critical threshold. "
            f"Error correction protocols may be applied to extract a secure key."
        )
    else:
        st.error(
            f"**Communication Compromised**\n\n"
            f"QBER of {results['qber']:.2f}% exceeds the security threshold of 11%. "
            f"The error rate is consistent with eavesdropping or excessive channel noise - "
            f"the protocol should be aborted and the channel investigated."
        )    

    st.markdown("---")

    # Transmission Phase
    st.header("Transmission Phase")
    
    # Table + Pie Chart
    col_trans_table, col_trans_chart = st.columns([1.2, 1])
    
    with col_trans_table:
        st.markdown("**Transmission Metrics**")
        transmission_df = pd.DataFrame({
            "Metric": [
                "Initial Qubits Transmitted",
                "Qubits Lost in Channel",
                "Photon Loss Rate",
                "Qubits Successfully Received",
                "Channel Transmission Efficiency"
            ],
            "Value": [
                results['initial_qubits'],
                results['lost_qubits'],
                f"{(results['lost_qubits']/results['initial_qubits']*100):.2f}%",
                results['received_qubits'],
                f"{(results['received_qubits']/results['initial_qubits']*100):.2f}%"
            ]
        })
        st.dataframe(transmission_df, hide_index=True, use_container_width=True)
    
    with col_trans_chart:
        st.markdown("**Channel Transmission**")
        
        # Pie chart showing received vs lost
        fig_trans_pie = go.Figure()
        
        fig_trans_pie.add_trace(go.Pie(
            labels=['Lost in Channel', 'Successfully Received'],  # Reversed order
            values=[results['lost_qubits'], results['received_qubits']],  # Reversed order
            marker=dict(
                colors=['#6B7280', '#10B981'],  # Gray first, Green second
                line=dict(width=0),
                pattern=dict(
                    shape=['/', ''],  # Hatching first, no pattern second
                    fgcolor=['#333333', 'rgba(0,0,0,0)']  # Reversed
                )
            ),
            texttemplate='%{percent:.2%}<br>%{value} qubits',
            textfont=dict(size=12, color='white'),
            direction='clockwise',
            sort=False,
            rotation=0,
            hovertemplate='%{label}: %{value} qubits (%{percent})<extra></extra>'
        ))
        
        fig_trans_pie.update_layout(
            margin=dict(l=20, r=20, t=10, b=50),
            height=250,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.20,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
                traceorder='reversed',
            )
        )
        
        st.plotly_chart(fig_trans_pie, use_container_width=True, key="transmission_pie")

# Bloch Sphere Visualization - Before and After
    st.subheader("Quantum State Visualization (Bloch Spheres)")
    
    col_before, col_after = st.columns(2)
    
    # Track the same qubit before and after transmission
    valid_indices = [i for i in range(len(qubits)) if i not in lost_indices]
    
    if len(valid_indices) > 0:
        # Pick one surviving qubit to track
        sample_idx = np.random.choice(valid_indices)
        position_after = sample_idx - np.sum(lost_indices < sample_idx)
        
        # Before Transmission
        with col_before:
            st.markdown("**Before Transmission (Alice's Prepared State)**")
            
            qc_before = qubits[sample_idx]
            state_before = Statevector.from_instruction(qc_before)
            
            basis_before = alice_bases_original[sample_idx]
            bit_before = alice_bits_original[sample_idx]
            basis_label_before = "Rectilinear" if basis_before == 0 else "Diagonal"
            
            # Determine proper state notation
            if basis_before == 0:  # Rectilinear
                state_name_before = f"|{bit_before}⟩"
            else:  # Diagonal
                state_name_before = "|+⟩" if bit_before == 0 else "|−⟩"
            
            bloch_fig_before, (x_b, y_b, z_b) = create_interactive_bloch_sphere(
                state_before, 
                f"Alice's State: {basis_label_before} {state_name_before}"
            )
            st.plotly_chart(bloch_fig_before, use_container_width=True, key="bloch_before")
            
            # Display Bloch vector values
            bloch_values_before = pd.DataFrame({
                "Component": ["X", "Y", "Z"],
                "Value": [f"{x_b:.2f}", f"{y_b:.2f}", f"{z_b:.2f}"]
            })
            st.dataframe(bloch_values_before, hide_index=True, use_container_width=True)
            st.caption(f"Prepared qubit #{sample_idx + 1}")
        
        # After Transmission
        with col_after:
            st.markdown("**After Transmission (With Noise/Eve)**")
            
            if position_after < len(noisy_qubits):
                qc_after = noisy_qubits[position_after]
                state_after = Statevector.from_instruction(qc_after)
                
                # Calculate Bloch coordinates first
                bloch_fig_temp, (x_a, y_a, z_a) = create_interactive_bloch_sphere(
                    state_after, 
                    "Calculating..."
                )
                
                # Get basis
                basis_after = alice_bases_after_loss[position_after]
                basis_label_after = "Rectilinear" if basis_after == 0 else "Diagonal"
                
                # Determine state from Bloch coordinates
                if abs(z_a - 1.0) < 0.1:
                    actual_state = "|0⟩"
                elif abs(z_a + 1.0) < 0.1:
                    actual_state = "|1⟩"
                elif abs(x_a - 1.0) < 0.1:
                    actual_state = "|+⟩"
                elif abs(x_a + 1.0) < 0.1:
                    actual_state = "|−⟩"
                else:
                    actual_state = "corrupted"
                
                # Create Bloch sphere
                bloch_fig_after, (x_a, y_a, z_a) = create_interactive_bloch_sphere(
                    state_after, 
                    f"After Channel: {basis_label_after} {actual_state}"
                )
                st.plotly_chart(bloch_fig_after, use_container_width=True, key="bloch_after")
                
                # Display Bloch vector values
                bloch_values_after = pd.DataFrame({
                    "Component": ["X", "Y", "Z"],
                    "Value": [f"{x_a:.2f}", f"{y_a:.2f}", f"{z_a:.2f}"]
                })
                st.dataframe(bloch_values_after, hide_index=True, use_container_width=True)
                st.caption(f"Qubit #{sample_idx + 1} after transmission")
    else:
        st.warning("No qubits survived transmission for Bloch sphere visualization")

    st.markdown("---")

    # Basis Selection distribution
    st.subheader("Basis Selection Distribution")
    
    # Row 1: Alice and Bob pie charts
    col_alice_pie, col_bob_pie = st.columns(2)
    
    with col_alice_pie:
        st.markdown("**Alice's Basis Selection**")

        
        alice_rectilinear = np.sum(alice_bases_original == 0)
        alice_diagonal = np.sum(alice_bases_original == 1)
        
        df_alice = pd.DataFrame({
            'Basis': ['Diagonal (|+⟩, |−⟩)', 'Rectilinear (|0⟩, |1⟩)'],
            'Count': [alice_diagonal, alice_rectilinear]
        })
        
        fig_alice = px.pie(
            df_alice, 
            values='Count', 
            names='Basis',
            color_discrete_map={
                'Rectilinear (|0⟩, |1⟩)': '#1E3A8A',
                'Diagonal (|+⟩, |−⟩)': '#3B82F6'
            }
        )
        
        fig_alice.update_traces(
            texttemplate='%{percent:.2%}<br>%{value} qubits',
            textfont=dict(size=12, color='white'),
            marker=dict(line=dict(width=0)),
            direction='clockwise',
            sort=False
        )
        
        fig_alice.update_layout(
            margin=dict(l=20, r=20, t=10, b=50),
            height=300,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.20,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
                traceorder='reversed'
            )
        )
        
        st.plotly_chart(fig_alice, use_container_width=True, key="alice_basis")
    
    with col_bob_pie:
        st.markdown("**Bob's Basis Selection**")
        
        bob_rectilinear = np.sum(bb84.bob_bases == 0)
        bob_diagonal = np.sum(bb84.bob_bases == 1)
        
        df_bob = pd.DataFrame({
            'Basis': ['Diagonal (|+⟩, |−⟩)', 'Rectilinear (|0⟩, |1⟩)'],
            'Count': [bob_diagonal, bob_rectilinear]
        })
        
        fig_bob = px.pie(
            df_bob, 
            values='Count', 
            names='Basis',
            color_discrete_map={
                'Rectilinear (|0⟩, |1⟩)': '#1E3A8A',
                'Diagonal (|+⟩, |−⟩)': '#3B82F6'
            }
        )
        
        fig_bob.update_traces(
            texttemplate='%{percent:.2%}<br>%{value} qubits',
            textfont=dict(size=12, color='white'),
            marker=dict(line=dict(width=0)),
            direction='clockwise',
            sort=False
        )
        
        fig_bob.update_layout(
            margin=dict(l=20, r=20, t=10, b=50),
            height=300,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.20,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
                traceorder='reversed'
            )
        )
        
        st.plotly_chart(fig_bob, use_container_width=True, key="bob_basis")
    
    # Basis Reconciliation Sankey
    st.markdown("**Basis Reconciliation**")
    
    # Calculate matching combinations
    matching_bases = np.sum(alice_bases_after_loss == bb84.bob_bases)
    total_received = len(alice_bases_after_loss)
    mismatched_bases = total_received - matching_bases
    
    # Count specific combinations
    both_rect = np.sum((alice_bases_after_loss == 0) & (bb84.bob_bases == 0))
    both_diag = np.sum((alice_bases_after_loss == 1) & (bb84.bob_bases == 1))
    alice_rect_bob_diag = np.sum((alice_bases_after_loss == 0) & (bb84.bob_bases == 1))
    alice_diag_bob_rect = np.sum((alice_bases_after_loss == 1) & (bb84.bob_bases == 0))
    mixed_bases = alice_rect_bob_diag + alice_diag_bob_rect
    
    # Calculate percentages
    both_rect_pct = (both_rect / total_received * 100)
    both_diag_pct = (both_diag / total_received * 100)
    mixed_pct = (mixed_bases / total_received * 100)
    matched_pct = (matching_bases / total_received * 100)
    mismatched_pct = (mismatched_bases / total_received * 100)
    
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="white", width=1),
            label=[
                f"Both Rectilinear<br>{both_rect_pct:.2f}%<br>{both_rect} qubits",
                f"Both Diagonal<br>{both_diag_pct:.2f}%<br>{both_diag} qubits",
                f"Mixed Bases<br>{mixed_pct:.2f}%<br>{mixed_bases} qubits",
                f"Matched<br>{matched_pct:.2f}%<br>{matching_bases} qubits<br>→ Sifted Key",
                f"Mismatched<br>{mismatched_pct:.2f}%<br>{mismatched_bases} qubits<br>→ Discarded"
            ],
            color=["#1E3A8A", "#3B82F6", "#94A3B8", "#10B981", "#6B7280"]
        ),
        link=dict(
            source=[0, 1, 2],
            target=[3, 3, 4],
            value=[both_rect, both_diag, mixed_bases],
            color=["rgba(16, 185, 129, 0.4)", "rgba(16, 185, 129, 0.4)", "rgba(107, 114, 128, 0.4)"]
        )
    )])
    
    fig_sankey.update_layout(
        margin=dict(l=0, r=0, t=10, b=20),
        height=300,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig_sankey, use_container_width=True, key="basis_sankey")
    
    st.markdown("---")

    # Error Detection Process
    if results['sifted_key_length'] > 0:
        st.subheader("Error Detection Breakdown")
                
        # Calculate values
        clean_sampled = results['sampled_bits'] - results['error_count']
        
        # Create grouped bar chart
        fig_error = go.Figure()
        
        # Bar 1: Sifted Key (dark blue)
        fig_error.add_trace(go.Bar(
            x=['Sifted Key'],
            y=[results['sifted_key_length']],
            marker_color='#1E3A8A',
            text=[f"100.00%<br>{results['sifted_key_length']} bits"],  # % on top, count on bottom
            textposition='outside',
            textfont=dict(size=12),
            showlegend=False
        ))
        
        # Bar 2: Bits Sampled (medium blue)
        fig_error.add_trace(go.Bar(
            x=['Sampled for Error Estimation'],
            y=[results['sampled_bits']],
            marker_color='#3B82F6',
            text=[f"{results['sampled_bits']/results['sifted_key_length']*100:.2f}%<br>{results['sampled_bits']} bits"],
            textposition='outside',
            textfont=dict(size=12),
            showlegend=False
        ))
        
        # Bar 3: Clean Bits (light blue)
        fig_error.add_trace(go.Bar(
            x=['Without Errors'],
            y=[clean_sampled],
            marker_color='#60A5FA',
            text=[f"{clean_sampled/results['sampled_bits']*100:.2f}%<br>{clean_sampled} bits"],
            textposition='outside',
            textfont=dict(size=12),
            showlegend=False
        ))
        
        # Bar 4: Errors (red)
        fig_error.add_trace(go.Bar(
            x=['Errors Detected'],
            y=[results['error_count']],
            marker_color='#EF4444',
            text=[f"{results['error_count']/results['sampled_bits']*100:.2f}%<br>{results['error_count']} bits"],
            textposition='outside',
            textfont=dict(size=12),
            showlegend=False
        ))
        
        # Calculate y-axis max
        max_val = results['sifted_key_length']
        if max_val <= 1000:
            y_max = int(np.ceil(max_val / 200) * 200)
            tick_interval = 200
        else:
            y_max = int(np.ceil(max_val / 1000) * 1000)
            tick_interval = 1000
        
        # Layout
        fig_error.update_layout(
            yaxis=dict(
                title='Number of Bits',
                titlefont=dict(size=12),
                range=[0, y_max * 1.15],
                tickmode='linear',
                tick0=0,
                dtick=tick_interval,
                tickformat='d',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            xaxis=dict(
                tickfont=dict(size=12)
            ),
            margin=dict(l=50, r=20, t=60, b=40),
            height=450,
            barmode='group',
            showlegend=False
        )
        
        st.plotly_chart(fig_error, use_container_width=True, key="error_bars")
               
    # Error Estimation Metrics table
    st.markdown("**Error Detection Breakdown Metrics**")
    
    if results['sifted_key_length'] == 0:
        st.warning("No sifted key generated")
    
    # Pre-processing table
    error_est_df = pd.DataFrame({
        "Stage": [
            "Sifted Key Length",
            "Bits Sampled for Error Estimation",
            "Errors Detected in Sample",
            "Quantum Bit Error Rate",
            "Bits Remaining for Post-Processing"
        ],
        "Value": [
            results['sifted_key_length'],
            results['sampled_bits'],
            results['error_count'],
            f"{results['qber']:.2f}%",
            results['intermediate_key_length']
        ]
    })
    st.dataframe(error_est_df, hide_index=True, use_container_width=True)
    
    # QBER Analysis and Security Assessment
    st.markdown("**Quantum Bit Error Rate Analysis and Security Assessment**")
    
    # Calculate theoretical QBER
    theoretical_qber = depolarization_prob * 100 * (2/3) if depolarization_prob > 0 else 0
    delta_from_threshold = results['qber'] - 11.0
    
    # Create horizontal bar chart
    fig_qber = go.Figure()
    
    # Bar 1: Theoretical QBER (blue)
    fig_qber.add_trace(go.Bar(
        y=['Theoretical QBER<br>(Noise Only)'],
        x=[theoretical_qber],
        orientation='h',
        marker_color='#3B82F6',
        text=[f"{theoretical_qber:.2f}%"],
        textposition='outside',
        textfont=dict(size=12),
        showlegend=False
    ))
    
    # Bar 2: Measured QBER (red if above threshold)
    measured_color = '#EF4444' if results['qber'] > 11 else '#1E3A8A'
    fig_qber.add_trace(go.Bar(
        y=['Measured QBER<br>(Actual)'],
        x=[results['qber']],
        orientation='h',
        marker_color=measured_color,
        text=[f"{results['qber']:.2f}%"],
        textposition='outside',
        textfont=dict(size=12),
        showlegend=False
    ))
    
    # Add security threshold vertical line
    fig_qber.add_vline(
        x=11,
        line_dash="dash",
        line_color="mediumspringgreen",
        line_width=3
    )
    
     # Invisible trace for legend
    fig_qber.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='lines',
        line=dict(color='mediumspringgreen', width=3, dash='dash'),
        name='Security Threshold (11%)',
        showlegend=True
    ))
    
    
    # Layout with legend at bottom left
    fig_qber.update_layout(
        xaxis=dict(
            title='QBER (%)',
            titlefont=dict(size=12),
            range=[0, max(results['qber'], theoretical_qber, 15) * 1.1],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        yaxis=dict(
            tickfont=dict(size=12)
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="right",  
            x=0.98,          
            font=dict(size=12)
        ),
        margin=dict(l=200, r=20, t=20, b=80),
        height=250,
        showlegend=True
    )
    
    st.plotly_chart(fig_qber, use_container_width=True, key="qber_comparison")
    
    st.markdown("**QBER Comparative Analysis**")
    # Simplified table
    qber_stats_df = pd.DataFrame({
        "Metric": [
            "Theoretical QBER (Noise Only)",
            "Measured QBER (Actual)",
            "Difference from Threshold"
        ],
        "Value": [
            f"{theoretical_qber:.2f}%",
            f"{results['qber']:.2f}%",
            f"{delta_from_threshold:+.2f}% ({'above' if delta_from_threshold > 0 else 'below'})"
        ]
    })
    
    st.dataframe(qber_stats_df, hide_index=True, use_container_width=True)


    
    # Visualizations
    st.markdown("---")
    st.header("Post-Processing")
    
    # Error Correction Statistics
    st.subheader("Step 1: Error Correction (CASCADE)")
    
    col_ec1, col_ec2, col_ec3 = st.columns(3)
    
    with col_ec1:
        st.metric(
            "Errors Corrected",
            results['errors_corrected'],
            help="Number of bit errors fixed by CASCADE algorithm"
        )
    
    with col_ec2:
        st.metric(
            "CASCADE Passes",
            results['cascade_passes'],
            help="Number of iterations performed"
        )
    
    with col_ec3:
        st.metric(
            "Bits Disclosed",
            results['bits_disclosed_ec'],
            delta=f"-{results['bits_disclosed_ec']/results['intermediate_key_length']*100:.2f}%" if results['intermediate_key_length'] > 0 else "0%",
            delta_color="inverse",
            help="Parity information leaked during error correction"
        )
    
    
    # Privacy Amplification Statistics
    st.subheader("Step 2: Privacy Amplification")
    
    col_pa1, col_pa2, col_pa3 = st.columns(3)
    
    with col_pa1:
        st.metric(
            "Binary Entropy H(QBER)",
            f"{results['binary_entropy']:.4f}",
            help="Shannon entropy based on error rate - measures Eve's information"
        )
    
    with col_pa2:
        st.metric(
            "Compression Ratio",
            f"{results['compression_ratio']*100:.2f}%",
            help="Fraction of key retained after removing Eve's information"
        )
    
    with col_pa3:
        st.metric(
            "Bits Removed",
            results['bits_removed_pa'],
            delta=f"-{results['bits_removed_pa']/results['after_error_correction']*100:.2f}%" if results['after_error_correction'] > 0 else "0%",
            delta_color="inverse",
            help="Bits removed to ensure information-theoretic security"
        )
    
    st.markdown("**Post-Processing Results**")

    post_proc_progression = pd.DataFrame({
    "Stage": [
        "CASCADE Error Correction",
        "Privacy Amplification",
        "Final Secure Key"
    ],
    "Key Length (bits)": [
        results['after_error_correction'],
        f"{results['after_error_correction']} → {results['final_key_length']}",
        results['final_key_length']
    ],
    "Operation": [
        f"Fixed {results['errors_corrected']} errors",
        f"Removed {results['bits_removed_pa']} bits",
        "-"
    ]
})
    st.dataframe(post_proc_progression, hide_index=True, use_container_width=True)

    
    st.markdown("---")

    # Full Protocol Pipeline
    st.subheader("Protocol Pipeline")

    # Pipeline stages
    stages = [
        'Initial\nQubits',
        'After\nChannel Loss',
        'After\nSifting',
        'After Sample\nDiscard',
        'After Error\nCorrection',
        'After Privacy\nAmplification'
    ]
    
    values = [
        results['initial_qubits'],
        results['received_qubits'],
        results['sifted_key_length'],
        results['intermediate_key_length'],
        results['after_error_correction'],
        results['final_key_length']
    ]
    
    # Plotly bar chart
    fig_pipeline = go.Figure()
    
    colors = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#10B981']
    
    for stage, value, color in zip(stages, values, colors):
        fig_pipeline.add_trace(go.Bar(
            x=[stage],
            y=[value],
            name=stage.replace('\n', ' '),
            marker_color=color,
            text=[f'{int(value)}'],
            textposition='outside',
            textfont=dict(size=12),
            hovertemplate=f'{stage.replace(chr(10), " ")}: {value} bits<extra></extra>',
            showlegend=False
        ))
    
    # Calculate y-axis max
    max_val = results['initial_qubits']
    if max_val <= 1000:
        y_max = int(np.ceil(max_val / 200) * 200)
        tick_interval = 200
    else:
        y_max = int(np.ceil(max_val / 1000) * 1000)
        tick_interval = 1000  
    
    # Layout
    fig_pipeline.update_layout(
        yaxis=dict(
            title='Number of Bits',
            titlefont=dict(size=12),
            range=[0, y_max * 1.05],
            tickmode='linear',
            tick0=0,
            dtick=tick_interval,
            tickformat='d',
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        xaxis=dict(
            tickfont=dict(size=12)
        ),
        margin=dict(l=50, r=20, t=60, b=40),
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig_pipeline, use_container_width=True, key="pipeline_chart") 
    

else:
    # Initial state
    st.header("Description")
    
    st.markdown("""
    
    This project is a simulation of the BB84 protocol over a noisy and lossy channel built with Qiskit and Streamlit. It attempts to model more realistic channel conditions using Qiskit to model quantum states and by applying configurable noise operators and an eavesdropper with an intercept-resend attack where their parameters can be adjusted to visualise and analyse their effects on QBER, key generation rate, final key length, and overall protocol security.""")
    
    st.markdown("""
    ### BB84 Protocol
    
    The BB84 protocol is a quantum key distribution (QKD) protocol developed by Bennett and Brassard that allows two parties (e.g. Alice and Bob) to securely generate a shared secret key over an insecure channel by encoding classical information into quantum states, transmitting them over a quantum channel, and then applying a series of classical post-processing steps to extract a secure key.
                
    Its security is based in the principles of quantum mechanics, namely the no-cloning theorem which states that it’s impossible to create an identical copy of an unknown quantum state, and measurement disturbance, where any attempt to observe the quantum state inherently alters it. Therefore, any attempt by an eavesdropper to intercept or measure the transmitted qubits introduces detectable disturbances in the system, allowing Alice and Bob to identify potential security breaches.
    """)
    
    
    col_steps1, col_steps2 = st.columns(2)
    
    with col_steps1:
        st.markdown("""
        ### Protocol Steps
                    
        **1. Quantum State Preparation**  
        Alice encodes random bits using randomly selected measurement bases (rectilinear or diagonal)
        
        **2. Quantum Transmission**  
        Qubits are transmitted through a quantum channel
        
        **3. Measurement**  
        Bob measures received qubits using his own randomly selected measurement bases
        
        **4. Basis Reconciliation**  
        Alice and Bob publicly compare bases and retain only matching measurements which form the sifted key
        """)
    
    with col_steps2:
        st.markdown("""
        ### &nbsp;
        **5. Error Estimation**  
        A 15% sample of the sifted key is compared to measure the Quantum Bit Error Rate (QBER)
        
        **6. Error Correction**  
        The CASCADE algorithm corrects bit errors through iterative binary search and parity checks
        
        **7. Privacy Amplification**  
        Universal hashing compresses the key to remove any information Eve might have gained
        
        **8. Final Secure Key**  
        Sampled bits are discarded to produce the final secure key
        """)
    
    
    st.markdown("""
    ### Simulation Parameters
            
    - **Number of Qubits:** Total number of qubits transmitted from Alice to Bob
            
    - **Depolarization:** Random Pauli gates (X, Y, Z) simulating quantum decoherence during transmission

    - **Photon Loss:** Random loss of photons (qubit erasure) simulating fiber attenuation and detection inefficiencies

    - **Eavesdropping:** Eve's intercept-resend attack 
    """)


    st.markdown("""
    Explore the effects of these parameters on the protocol's performance and security by adjusting them in the sidebar and observing the resulting metrics, visualizations, and security assessments.
    """)


# Footer
    st.markdown("---")
