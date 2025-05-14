---
title: "Signing Artifacts in Larger CI/CD ecosystems"
date: 2025-05-13T07:36:00-04:00
draft: false
categories: ["helm", "supply chain"]
tags: ["helm", "kubernetes", "cosign", "signature", "supply chain"]
---

## Supply Chain Security with Digital Signatures

Implementing digital signatures in CI/CD pipelines provides a crucial layer of verification and authenticity for artifacts as they move through your development ecosystem.

## Diagram: Artifact Signing Process Flow

```mermaid
sequenceDiagram
    participant Developer
    participant BuildSystem
    participant Registry
    participant PlatformTeam
    participant Customer

    Developer->>BuildSystem: 1. Commit Code (triggers build)
    Note left of Developer: "The Kitchen" – developers codebase
    BuildSystem->>BuildSystem: 2. Build Image + Generate Attestation
    BuildSystem->>Registry: 3. Push Image (tag:dev)
    BuildSystem->>Registry: 4. Sign Image (cosign + dev.key)
    BuildSystem->>Registry: 5. Attach Provenance Attestation (signed)

    PlatformTeam->>Registry: 6. Pull Image & Attestation
    PlatformTeam->>PlatformTeam: 7. Verify Developer Signature
    PlatformTeam->>PlatformTeam: 8. Verify Attestation (cosign verify-attestation)
    Note right of PlatformTeam: Checks build provenance:<br/>- Source repo<br/>- Build command<br/>- Commit hash<br/>- Builder identity

    alt Attestation Valid
        PlatformTeam->>Registry: 9. Sign with Platform Key (prod-tag)
    else Attestation Invalid
        PlatformTeam-->>Developer: 🔒 Reject: Build provenance mismatch
    end

    Customer->>Registry: 10. Pull Image (prod-tag)
    Customer->>Customer: 11. Verify Platform Signature (platform.pub)
```

The diagram above illustrates the flow of artifacts through a typical CI/CD pipeline, highlighting the signing and verification steps.

Now continuing the overall setup, if you had end users you were distributing artifacts (OCI compliant) to, then what would the entire sequence look like end-to-end? 

> I use AWS KMS in this example, but any key_types (keyless, asym-keys, cloud-KMS, cloudHSM, etc) are supported by Cosign. 

```mermaid
%%{init: {'theme': 'forest', 'themeVariables': { 'primaryColor': '#BB2528', 'primaryTextColor': '#fff', 'primaryBorderColor': '#7C0000', 'lineColor': '#F8B229', 'secondaryColor': '#006100'}}}%%
sequenceDiagram
    autonumber

    participant GT as Governance Team
    participant C_KMS as Cosign Private Key Store (e.g. AWS KMS)
    participant PGP_KS as PGP Private Key Store
    participant CDN as Public Key CDN (cdn.customer.com)
    participant AWS_DA as AWS Distribution Account
    participant ECR as Amazon ECR
    participant ENG as Engineer
    participant H_Repo as Helm Chart Repository
    participant User as End User

    rect rgb(230, 230, 250)
        note over GT C_KMS CDN: Section 1: Cosign Key Management & Publication
        GT->>GT: 1. Perform Cosign Key Ceremony (Multi-Member)
        GT->>C_KMS: 2. Generate & Store Asymmetric Key Pair (Private/Public)
        note right of C_KMS: Cosign Private Key securely stored in KMS.
        C_KMS-->>GT: 3. Confirmation / Public Key
        GT->>CDN: 4. Publish Cosign Public Key (e.g. .../pubkey-YYYY-MM-DD.pem)
        note right of CDN: Public key for image verification.
        note over GT C_KMS: Cosign Keys are rotated every 90 days. Steps 1-4 repeat.
    end

    rect rgb(200, 250, 200)
        note over AWS_DA ECR User: Section 2: Container Image Provenance & User Verification
        AWS_DA->>AWS_DA: 5. Build Container Image
        AWS_DA->>AWS_DA: 6. Generate SBOM for Image
        AWS_DA->>C_KMS: 7. Request to Sign Image & SBOM
        C_KMS-->>AWS_DA: 8. Signing Operation performed using Cosign Private Key
        AWS_DA->>AWS_DA: 9. Image & SBOM are now Signed with Cosign
        AWS_DA->>ECR: 10. Push Image, Signature, and SBOM to ECR
        note right of ECR: Container image, its signature, and SBOM are stored.

        User->>ECR: 11. Fetch Container Image
        User->>ECR: 12. Fetch Image Signature & SBOM
        User->>CDN: 13. Fetch Cosign Public Key (e.g. .../pubkey-YYYY-MM-DD.pem)
        User->>User: 14. Verify Image & SBOM (using 'cosign verify')
        note right of User: Verification confirms image integrity & provenance.
    end

    rect rgb(250, 230, 230)
        note over GT PGP_KS CDN: Section 3: PGP Key Management & Publication (for Helm)
        GT->>GT: 15. Perform PGP Key Ceremony (Multi-Member)
        GT->>PGP_KS: 16. Generate & Store PGP Key Pair
        note right of PGP_KS: PGP Private Key securely stored.
        PGP_KS-->>GT: 17. Confirmation / Public Keyring
        GT->>CDN: 18. Publish PGP Public Keyring (e.g. .../keyring-YYYY-MM-DD-FINGERPRINT.gpg)
        note right of CDN: Public keyring for Helm chart verification.
    end

    rect rgb(250, 250, 200)
        note over ENG H_Repo User: Section 4: Helm Chart Provenance & User Verification
        ENG->>ENG: 19. Develop Helm Chart
        ENG->>ENG: 20. Package Helm Chart (.tgz)
        ENG->>PGP_KS: 21. Request to Sign Helm Chart
        PGP_KS-->>ENG: 22. Signing Operation performed using PGP Private Key
        ENG->>ENG: 23. Helm Chart Signed with PGP (creates .prov file)
        ENG->>H_Repo: 24. Publish Chart (.tgz) & Provenance File (.prov)
        note right of H_Repo: Helm chart & its .prov file are stored.

        User->>H_Repo: 25. Fetch Helm Chart (.tgz)
        User->>H_Repo: 26. Fetch Provenance File (.prov)
        User->>CDN: 27. Fetch PGP Public Keyring (e.g. .../keyring-YYYY-MM-DD-FINGERPRINT.gpg)
        User->>User: 28. Import PGP Keyring locally
        User->>User: 29. Verify Helm Chart (using 'helm verify')
        note right of User: Verification confirms chart integrity & provenance.
    end
```
