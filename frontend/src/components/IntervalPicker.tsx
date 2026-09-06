import "./IntervalPicker.css";

interface Props {
  intervals: string[];
  value: string;
  onChange: (interval: string) => void;
  bars: number;
  onBarsChange: (bars: number) => void;
  showVolume: boolean;
  onShowVolumeChange: (value: boolean) => void;
  showMovingAverages: boolean;
  onShowMovingAveragesChange: (value: boolean) => void;
}

const BAR_CHOICES = [200, 500, 1000];

export function IntervalPicker({
  intervals,
  value,
  onChange,
  bars,
  onBarsChange,
  showVolume,
  onShowVolumeChange,
  showMovingAverages,
  onShowMovingAveragesChange,
}: Props) {
  return (
    <div className="controls panel">
      <fieldset className="controls__group">
        <legend className="controls__legend">INTERVAL</legend>
        {intervals.map((interval) => (
          <button
            key={interval}
            type="button"
            className={`controls__chip${interval === value ? " controls__chip--on" : ""}`}
            onClick={() => onChange(interval)}
            aria-pressed={interval === value}
          >
            {interval.toUpperCase()}
          </button>
        ))}
      </fieldset>

      <fieldset className="controls__group">
        <legend className="controls__legend">BARS</legend>
        {BAR_CHOICES.map((choice) => (
          <button
            key={choice}
            type="button"
            className={`controls__chip${choice === bars ? " controls__chip--on" : ""}`}
            onClick={() => onBarsChange(choice)}
            aria-pressed={choice === bars}
          >
            {choice}
          </button>
        ))}
      </fieldset>

      <fieldset className="controls__group">
        <legend className="controls__legend">OVERLAY</legend>
        <button
          type="button"
          className={`controls__chip${showVolume ? " controls__chip--on" : ""}`}
          onClick={() => onShowVolumeChange(!showVolume)}
          aria-pressed={showVolume}
        >
          VOL
        </button>
        <button
          type="button"
          className={`controls__chip${showMovingAverages ? " controls__chip--on" : ""}`}
          onClick={() => onShowMovingAveragesChange(!showMovingAverages)}
          aria-pressed={showMovingAverages}
        >
          MA 50/200
        </button>
      </fieldset>
    </div>
  );
}
