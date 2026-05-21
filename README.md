### Quantum Key Distribution Simulation of the BB84 Protocol Over A Noisy and Lossy Channel

This project is a simulation of the BB84 protocol over a noisy and lossy channel built with Qiskit and Streamlit. It attempts to model more realistic channel conditions using Qiskit to model quantum states and by applying configurable noise operators and an eavesdropper with an intercept-resend attack where their parameters can be adjusted to visualise and analyse their effects on QBER, key generation rate, final key length, and overall protocol security.

### Features

* Complete implementation of the BB84 protocol
* Realistic channel impairment modeling (depolarization + photon loss)
* Eavesdropping detection (intercept-resend attack)
* CASCADE error correction + Privacy amplification
* Interactive Visualization
* Real-time security assessment

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/muegi/qkd-simulation.git
   cd bb84-qkd-simulation
   ```
2. Create virtual environment
   ```sh
   python -m venv venv
   ```
3. Activate
   ```sh
   venv\Scripts\activate or source venv/bin/activate for macOS/Linux
   ```
4. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```
5. Run Simulation
   ```sh
   streamlit run app.py
   ```
