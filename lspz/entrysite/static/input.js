
class LspzAudioPlayer {
  constructor(letter) {
    this.letter = letter;
    this.element = document.getElementById(`sample-${letter}`);
    this.description = document.getElementById(`sample-details-${letter}`);
    this.data_url = null;
    this.last_set_volume = 1; // (of 100, just to be safe);
  }

  mark_loading() {
    // TODO if ever?
  }

  load_track(track_id) {
    this.track_id = track_id;
    console.log(`Player is loading track ${track_id}`);

    this.description.innerHTML = "Loading track details...";
    jQuery.get(`/api/v1/track/${track_id}.html`, (data) => {
      this.description.innerHTML = data;
    }).fail(() => {
      this.description.innerHTML = `Failed to load, please report an error for ${track_id}`
    });

    jQuery.get(`/api/v1/track/${track_id}/gain`, (data) => {
      this.replaygain = data["track"];
      this.setVolume(this.last_set_volume);
    }).fail(() => {
      alert(`Failed to get replay gain for ${track_id}, track volume may be overly loud or quiet.`);
    });

    let el_source = this.element.getElementsByTagName('source')[0];
    el_source.src = `/api/v1/track/${track_id}/file`;
    this.element.load();
    if (!this.element.paused) this.element.pause();

  }

  /**
   * set volume while adjusting for replaygain if available
   * @param {level} level  0-100 human volume level
   */
  setVolume(level) {
    if (this.replaygain) {
      let adjustment = Math.pow(10.0, this.replaygain / 20);
      this.element.volume = adjustment * (level/100);
      console.log(`Adjusted volume for player ${this.letter} to ${this.element.volume}`);
    }
    else {
      this.element.volume = level / 100;
    }

    this.last_set_volume = level;
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
  player_a = new LspzAudioPlayer('a');
  player_b = new LspzAudioPlayer('b');

  let volume = localStorage.getItem("master_volume");

  if (volume) {
    console.log(`Restore user's volume preference to ${volume}`);
    vol_slider.value = volume;
  }
  setVolumeLevels(vol_slider.value);

  vol_slider.addEventListener("input", (e) => {
    console.debug(`master volume to ${vol_slider.value}`);
    setVolumeLevels(vol_slider.value);
    localStorage.setItem("master_volume", vol_slider.value);
  });

  // pause other track
  [[player_a, player_b], [player_b, player_a]].forEach((p) => {
    let first = p[0], second = p[1];
    first.element.addEventListener('play', (e) => {
      if (!second.element.paused) second.element.pause();
    });
  });

  // comparison adjectives for sliders
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

  jQuery("#lspz-data-submission").submit(function (e) {
    e.preventDefault();
    jQuery("#lspz-data-submission .btn[type='submit']").html("Submitting...");
    jQuery("#lspz-data-submission .btn[type='submit']").toggleClass(["btn-primary", "btn-outline-primary"]);

    // disable inputs:
    jQuery("#lspz-data-submission input").prop('disabled', true);
    jQuery("#lspz-data-submission button[type='submit']").prop('disabled', true);

    let form = jQuery(this),
        url = form.attr("action");

    let formData = new FormData(document.getElementById("lspz-data-submission"));
    formData.append("a", player_a.track_id);
    formData.append("b", player_b.track_id);

    jQuery.ajax({
      url: url,
      type: "post",
      data: formData,
      processData: false,
      contentType: false,
      success: (data) => {
        console.log(data);
        jQuery("#lspz-data-submission .btn[type='submit']").html("Submitted!");
        jQuery("#lspz-data-submission .btn[type='submit']").toggleClass(["btn-success", "btn-outline-primary"]);
        jQuery("#lspz-data-submission .btn#lspz-new").toggleClass(["btn-outline-danger", "btn-primary"]);
      },
      error: (r) => {
        alert("Failed to post submission.");
      },
    });

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
