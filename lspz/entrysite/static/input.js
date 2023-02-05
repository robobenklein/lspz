
class LspzAudioPlayer {
  constructor(element) {
    this.element = element;
    this.data_url = null;
  }

  load_track(data_url) {
    this.data_url = data_url;
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
  "vastly",
  "extremely",
];

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
}

window.addEventListener("load", lspz_loaded);
