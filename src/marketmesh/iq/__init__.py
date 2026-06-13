"""Microsoft IQ integration layer.

Three intelligence layers, each with a live path and a deterministic offline fallback
so the demo always runs:

  * ``fabric_iq``  — semantic product ontology / knowledge graph across vendors.
  * ``foundry_iq`` — grounded retrieval over product knowledge (cited answers).
  * ``work_iq``    — Microsoft 365 buyer signals (demand, renewals, approvals).
"""
