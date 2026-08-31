// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IdentityAttestation
 * @dev Cryptographic registry for anchoring and verifying facial scan to social media discovery attestations.
 */
contract IdentityAttestation {
    
    struct Attestation {
        bytes32 payloadHash;       // Keccak256 hash of canonical social media post metadata
        bytes32 faceHash;          // Keccak256 hash of facial embedding & image fingerprints
        address submitter;         // Address that submitted the attestation
        uint256 blockTimestamp;    // Block timestamp when anchored
        string metadataUri;        // Decentralized storage URI (e.g., ipfs:// CID or URI)
        bool isAnchored;           // Existence flag
    }

    // Mapping from payloadHash to on-chain Attestation
    mapping(bytes32 => Attestation) private _attestations;
    
    // Array of all anchored payload hashes for enumeration
    bytes32[] private _allPayloadHashes;

    // Events
    event AttestationAnchored(
        bytes32 indexed payloadHash,
        bytes32 indexed faceHash,
        address indexed submitter,
        uint256 timestamp,
        string metadataUri
    );

    error AttestationAlreadyExists(bytes32 payloadHash);
    error AttestationNotFound(bytes32 payloadHash);

    /**
     * @notice Anchor a new face-to-social attestation to the blockchain.
     * @param payloadHash Keccak256 hash of the canonical social media payload.
     * @param faceHash Keccak256 hash of the facial vector and image data.
     * @param metadataUri IPFS CID or metadata reference URI.
     */
    function anchorAttestation(
        bytes32 payloadHash,
        bytes32 faceHash,
        string calldata metadataUri
    ) external returns (bytes32) {
        require(payloadHash != bytes32(0), "Invalid payload hash");
        require(faceHash != bytes32(0), "Invalid face hash");

        if (_attestations[payloadHash].isAnchored) {
            revert AttestationAlreadyExists(payloadHash);
        }

        _attestations[payloadHash] = Attestation({
            payloadHash: payloadHash,
            faceHash: faceHash,
            submitter: msg.sender,
            blockTimestamp: block.timestamp,
            metadataUri: metadataUri,
            isAnchored: true
        });

        _allPayloadHashes.push(payloadHash);

        emit AttestationAnchored(
            payloadHash,
            faceHash,
            msg.sender,
            block.timestamp,
            metadataUri
        );

        return payloadHash;
    }

    /**
     * @notice Verify if a payload hash is registered on-chain and retrieve its cryptographic record.
     * @param payloadHash Keccak256 hash of the payload to verify.
     */
    function verifyAttestation(bytes32 payloadHash)
        external
        view
        returns (
            bool exists,
            uint256 blockTimestamp,
            address submitter,
            bytes32 faceHash,
            string memory metadataUri
        )
    {
        Attestation memory record = _attestations[payloadHash];
        if (!record.isAnchored) {
            return (false, 0, address(0), bytes32(0), "");
        }
        return (
            true,
            record.blockTimestamp,
            record.submitter,
            record.faceHash,
            record.metadataUri
        );
    }

    /**
     * @notice Get full attestation struct.
     */
    function getAttestation(bytes32 payloadHash) external view returns (Attestation memory) {
        if (!_attestations[payloadHash].isAnchored) {
            revert AttestationNotFound(payloadHash);
        }
        return _attestations[payloadHash];
    }

    /**
     * @notice Returns total number of anchored attestations.
     */
    function getTotalAttestations() external view returns (uint256) {
        return _allPayloadHashes.length;
    }
}
