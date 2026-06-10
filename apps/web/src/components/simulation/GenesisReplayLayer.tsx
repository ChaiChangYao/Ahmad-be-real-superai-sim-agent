"use client";



import { useFrame } from "@react-three/fiber";

import { useMemo, useRef } from "react";

import { Group, Quaternion, Vector3 } from "three";

import { clampFrameIndex } from "@/lib/playback";

import { useSimStore } from "@/lib/state";

import { convertPosition, convertQuaternion } from "@/components/genesis-workbench/replay/replay_transforms";

import { RobotDogPreview } from "./RobotDogPreview";



const STAND_INPUT = {

  forward: false,

  backward: false,

  left: false,

  right: false,

  jump: false,

  stop: false,

  resetTick: 0,

};



function frameRobotTransform(frame: Record<string, unknown> | null): { position: Vector3; quaternion: Quaternion } | null {

  if (!frame) return null;

  const entities = frame.entities as Record<string, Record<string, unknown>> | undefined;

  const robot = entities?.robot ?? entities?.target;

  const links = frame.links as Record<string, { position?: number[]; rotation_quat?: number[] }> | undefined;

  const body = links?.body;

  const posArr = (robot?.position as number[] | undefined) ?? body?.position;

  const quatArr = (robot?.rotation_quat as number[] | undefined) ?? body?.rotation_quat;

  if (!posArr || posArr.length < 3) return null;

  const [tx, ty, tz] = convertPosition(posArr, "z");

  const position = new Vector3(tx, ty, tz);

  const quaternion = new Quaternion();

  const converted = convertQuaternion(quatArr, "z");

  if (converted) {

    quaternion.set(converted[0], converted[1], converted[2], converted[3]);

  }

  return { position, quaternion };

}



type GenesisReplayLayerProps = {

  showVisualMesh?: boolean;

  showCollisionMesh?: boolean;

  showJointAxes?: boolean;

  showSensorRays?: boolean;

  showWires?: boolean;

  showInternals?: boolean;

};



export function GenesisReplayLayer({

  showVisualMesh = true,

  showCollisionMesh = false,

  showJointAxes = false,

  showSensorRays = false,

  showWires = true,

  showInternals = false,

}: GenesisReplayLayerProps) {

  const runTimeseries = useSimStore((s) => s.runTimeseries);

  const playbackFrameIndex = useSimStore((s) => s.playbackFrameIndex);

  const playbackPlaying = useSimStore((s) => s.playbackPlaying);

  const rootRef = useRef<Group>(null);

  const autoIndexRef = useRef(0);



  const hasReplay = runTimeseries.length > 0;

  const scrubIndex = clampFrameIndex(playbackFrameIndex, runTimeseries.length);



  useFrame((_, delta) => {

    if (!rootRef.current || !hasReplay) return;

    let frameIndex = scrubIndex;

    if (playbackPlaying) {

      autoIndexRef.current = (autoIndexRef.current + delta * 30) % runTimeseries.length;

      frameIndex = Math.floor(autoIndexRef.current);

    }

    const transform = frameRobotTransform(runTimeseries[frameIndex] as Record<string, unknown>);

    if (!transform) return;

    rootRef.current.position.copy(transform.position);

    rootRef.current.quaternion.copy(transform.quaternion);

  });



  const initial = useMemo(

    () => frameRobotTransform(runTimeseries[scrubIndex] as Record<string, unknown>),

    [runTimeseries, scrubIndex]

  );



  if (!hasReplay) return null;



  return (

    <group ref={rootRef} position={initial?.position ?? [0, 0.5, 0]} quaternion={initial?.quaternion}>

      <RobotDogPreview

        input={STAND_INPUT}

        showVisualMesh={showVisualMesh}

        showCollisionMesh={showCollisionMesh}

        showJointAxes={showJointAxes}

        showSensorRays={showSensorRays}

        showWires={showWires}

        showInternals={showInternals}

      />

    </group>

  );

}

