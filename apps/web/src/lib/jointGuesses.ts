import type { BuildablesJoint } from "@schemas/types";

export type JointGuess = {
  id: string;
  joint_type: string;
  parent_link_id: string;
  child_link_id: string;
  origin_xyz: number[];
  axis_xyz: number[];
  limit_lower_rad: number;
  limit_upper_rad: number;
  confidence: number;
  reasons: string[];
  needs_user_confirmation: boolean;
};

export function guessToManifestJoint(guess: JointGuess, existingId?: string): BuildablesJoint {
  const [ox, oy, oz] = guess.origin_xyz;
  const [ax, ay, az] = guess.axis_xyz;
  const jointType = guess.joint_type === "prismatic" ? "prismatic" : guess.joint_type === "fixed" ? "fixed" : "revolute";
  return {
    id: existingId ?? guess.id.replace(/^guess-/, "j-"),
    name: `${guess.parent_link_id}_to_${guess.child_link_id}`,
    type: jointType,
    parent_link_id: guess.parent_link_id,
    child_link_id: guess.child_link_id,
    origin_xyz: { x: ox, y: oy, z: oz },
    origin_rpy: { x: 0, y: 0, z: 0 },
    axis_xyz: { x: ax, y: ay, z: az },
    limit_lower_rad: guess.limit_lower_rad,
    limit_upper_rad: guess.limit_upper_rad,
    effort_limit_nm: 20,
    velocity_limit_rad_s: 4,
    damping: 0.1,
    friction: 0.02,
    auto_detected: true,
    user_confirmed: true,
    notes: `Auto-guessed (confidence ${guess.confidence})`
  };
}
