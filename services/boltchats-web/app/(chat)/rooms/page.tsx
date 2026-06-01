// /rooms index — show empty state, layout handles auth guard
import type React from 'react';

export default function RoomsIndexPage(): React.JSX.Element {
  return (
    <div className="flex flex-1 flex-col items-center justify-center text-zinc-600 select-none">
      <p className="text-sm">Select a channel to start chatting</p>
    </div>
  );
}
