import { useEffect, useRef } from 'react';

interface SoundOptions {
  volume?: number;
  playbackRate?: number;
}

export function useSound(url: string, options: SoundOptions = {}) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { volume = 0.5, playbackRate = 1 } = options;

  useEffect(() => {
    // Only create audio in browser environment
    if (typeof window !== 'undefined') {
      const audio = new Audio(url);
      audio.volume = volume;
      audio.playbackRate = playbackRate;
      audioRef.current = audio;
      
      return () => {
        // Clean up
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }
      };
    }
  }, [url, volume, playbackRate]);

  const play = () => {
    if (audioRef.current) {
      // Reset the audio to the beginning
      audioRef.current.currentTime = 0;
      
      // Play the sound
      const playPromise = audioRef.current.play();
      
      // Handle potential play() promise rejection
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          console.error('Audio play failed:', error);
        });
      }
    }
  };

  const stop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  return { play, stop };
}
