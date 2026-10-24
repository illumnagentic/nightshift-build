import {
  motion,
  useDragControls,
  useMotionValue,
  useReducedMotion,
  useTransform,
  type PanInfo,
} from "motion/react";
import { useRef, type PointerEvent, type ReactNode } from "react";

const DISTANCE_RATIO = 0.3;
const VELOCITY = 600;

type Props = {
  children: ReactNode;
  disabled: boolean;
  onSwipe: (action: "left" | "right") => void;
};

export function SwipeableCard({ children, disabled, onSwipe }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const controls = useDragControls();
  const reduced = useReducedMotion();
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 0, 200], reduced ? [0, 0, 0] : [-8, 0, 8]);
  const likeOpacity = useTransform(x, [20, 100], [0, 1]);
  const dislikeOpacity = useTransform(x, [-100, -20], [1, 0]);

  function onPointerDown(e: PointerEvent<HTMLDivElement>) {
    if (disabled) return;
    if (e.target instanceof Element && e.target.closest("button")) return;
    controls.start(e);
  }

  function onDragEnd(_: unknown, info: PanInfo) {
    if (disabled) return;
    const width = ref.current?.offsetWidth ?? 0;
    const far = Math.abs(info.offset.x) > width * DISTANCE_RATIO;
    const fast = Math.abs(info.velocity.x) > VELOCITY;
    if (!far && !fast) return;
    onSwipe(info.offset.x < 0 ? "left" : "right");
  }

  return (
    <motion.div
      ref={ref}
      className="swipeable-card"
      drag="x"
      dragListener={false}
      dragControls={controls}
      dragSnapToOrigin
      dragElastic={0.6}
      style={{ x, rotate }}
      onPointerDown={onPointerDown}
      onDragEnd={onDragEnd}
    >
      {children}
      <motion.span
        className="swipeable-card__cue swipeable-card__cue--like"
        style={{ opacity: likeOpacity }}
        aria-hidden="true"
      >
        Like
      </motion.span>
      <motion.span
        className="swipeable-card__cue swipeable-card__cue--dislike"
        style={{ opacity: dislikeOpacity }}
        aria-hidden="true"
      >
        Dislike
      </motion.span>
    </motion.div>
  );
}
