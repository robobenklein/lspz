
class LspzAudioPlayer {
  constructor(element) {
    this.element = element;
    this.data_url = null;
  }

  mark_loading() {

  }

  load_track(track_id) {
    this.track_id = track_id;
    console.log(`Player is loading track ${track_id}`);

    let el_source = this.element.getElementsByTagName('source')[0];
    el_source.src = `/api/v1/data/track/${track_id}/file`;
    this.element.load();
    if (!this.element.paused) this.element.pause();
  }

  /**
   * set volume while adjusting for replaygain if available
   * @param {level} level  0-100 human volume level
   */
  setVolume(level) {
    if (this.replaygain) {
      // TODO
    }
    else {
      this.element.volume = level / 100;
    }
  }
}

var vol_slider;
var player_a, player_b;

const comparison_adjectives = [
  "no",
  "barely",
  "slightly",
  "moderately",
  "substantially",
  // "vastly",
  "extremely",
];

// Track / Sample A contains ...
const vocal_amounts = [
  "no evidence of a voice at all.",
  "human voice-like sounds, but without any recognizable language.",
  "recognizably human vocal sounds, but without any use of language. (e.g. vocal stabs)",
  "human voices, perhaps words, but not substantially.",
  "recognizable human speech or singing. (in any language)",
  "clear, recognizable lyrics. (in any language)",
  "substantial lyrics, which make up the majority of the audio.",
]

/**
 * set volume across both tracks while applying replaygain difference
 * @param {number} level 0 to 100
 */
function setVolumeLevels(level) {
  player_a.setVolume(level);
  player_b.setVolume(level);
}

function lspz_loaded (event) {
  console.log(`LSPZ load.`);

  vol_slider = document.getElementById("master_volume");
  player_a = new LspzAudioPlayer(document.getElementById("sample-a"));
  player_b = new LspzAudioPlayer(document.getElementById("sample-b"));

  let volume = localStorage.getItem("master_volume");

  if (volume) {
    console.log(`Restore user's volume preference to ${volume}`);
    vol_slider.value = volume;
    setVolumeLevels(volume);
  }

  vol_slider.addEventListener("input", (e) => {
    console.debug(`master volume to ${vol_slider.value}`);
    setVolumeLevels(vol_slider.value);
    localStorage.setItem("master_volume", vol_slider.value);
  });

  ["input_energy", "input_synthetic"].forEach(id => {
    var input_el = document.getElementById(id);
    var input_detail = document.getElementById(`${id}_detail`);

    let upfunc = () => {
      let val = input_el.value;
      let strength = Math.abs(val);
      let adj = comparison_adjectives[(strength * (comparison_adjectives.length-1)).toFixed()];
      input_detail.innerHTML = `${adj} ${val < 0 ? 'more' : 'less'}`;
    }
    input_el.addEventListener("input", upfunc);
    upfunc();
  });

  // finally, start loading the real input:
  lspz_load_samples();
}

window.addEventListener("load", lspz_loaded);

function lspz_load_samples() {
  player_a.mark_loading();
  player_b.mark_loading();

  jQuery.get("/api/v1/random/tracks/2", (data) => {
    let trackid_a = data[0];
    let trackid_b = data[1];

    player_a.load_track(trackid_a);
    player_b.load_track(trackid_b);
  });
}
