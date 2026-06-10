from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


KEYWORDS = ("hip", "knee", "ankle", "shoulder", "elbow", "wrist", "leg", "upper", "lower", "servo", "wheel", "hinge")


def auto_guess_joints(manifest: BuildablesPhysicsManifest) -> list[dict]:
    guesses: list[dict] = []
    links = manifest.links
    for parent in links:
        for child in links:
            if parent.id == child.id:
                continue
            child_name = child.name.lower()
            parent_name = parent.name.lower()
            confidence = 0.2
            reasons: list[str] = []
            if any(k in child_name for k in KEYWORDS):
                confidence += 0.25
                reasons.append("child link name contains joint-related keyword")
            if parent.category == "body" and child.category == "leg":
                confidence += 0.25
                reasons.append("body to leg attachment pattern")
            if parent.id.split("_")[0] == child.id.split("_")[0]:
                confidence += 0.2
                reasons.append("symmetry naming prefix matched")
            dx = abs(parent.transform.position.x - child.transform.position.x)
            dy = abs(parent.transform.position.y - child.transform.position.y)
            dz = abs(parent.transform.position.z - child.transform.position.z)
            if dx + dy + dz < 0.35:
                confidence += 0.2
                reasons.append("links are spatially close")
            if confidence < 0.5:
                continue
            jid = f"guess-{parent.id}-{child.id}"
            guess_type = "revolute"
            if "knee" in child_name:
                axis = [1.0, 0.0, 0.0]
            elif "hip" in child_name:
                axis = [0.0, 1.0, 0.0]
            else:
                axis = [1.0, 0.0, 0.0]
            guesses.append(
                {
                    "id": jid,
                    "joint_type": guess_type,
                    "parent_link_id": parent.id,
                    "child_link_id": child.id,
                    "origin_xyz": [child.transform.position.x, child.transform.position.y, child.transform.position.z],
                    "axis_xyz": axis,
                    "limit_lower_rad": -1.0,
                    "limit_upper_rad": 1.0,
                    "confidence": round(min(confidence, 0.95), 2),
                    "reasons": reasons,
                    "needs_user_confirmation": True,
                }
            )
    guesses.sort(key=lambda g: g["confidence"], reverse=True)
    return guesses[:24]
