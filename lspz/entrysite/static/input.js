
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

class LspzAudioSettings {
  constructor() {
    this.functions = {};
  }

  registerSetting(name, defaultval) {
    if (localStorage.getItem(name) === null) {
      localStorage.setItem(name, JSON.stringify(defaultval));
    }
  }

  /**
   * set a function to be called with values of a setting
   * @param {[type]} name      setting key
   * @param {[type]} function  function(cur_value)
   */
  addCallback(name, func, call_now = false) {
    if (!this.functions[name]) this.functions[name] = [];
    this.functions[name].push(func);
    if (call_now) {
      func(this.getItem(name));
    }
  }

  getItem(name) {
    return JSON.parse(localStorage.getItem(name));
  }

  setItem(name, value) {
    localStorage.setItem(name, JSON.stringify(value));
    if (this.functions[name] && this.functions[name].length) this.functions[name].forEach(
      (f) => f(value)
    );
  }
}

function objectifyForm(formArray) {
  var returnArray = {};
  for (var i = 0; i < formArray.length; i++){
    returnArray[formArray[i]['name']] = formArray[i]['value'];
  }
  return returnArray;
}

var vol_slider;
var lspz_settings = new LspzAudioSettings();
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
  "...",
  "no evidence of a voice at all.",
  "sounds similar to a human voice.",
  "recognizably human vocal sounds, but no language.",
  "human voices, perhaps words, but no lyrics.",
  "recognizable human speech or singing. (in any language)",
  "clear, recognizable lyrics. (in any language)",
  "substantial or dominant lyrics.",
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

  for (let key in init_settings) {
    let defaultval = init_settings[key];
    lspz_settings.registerSetting(key, false);
    let switch_el = document.getElementById(key);
    switch_el.checked = lspz_settings.getItem(key);
    console.debug(`Restore ${key} to ${lspz_settings.getItem(key)}`);

    switch_el.addEventListener("click", (e) => {
      console.log(e, switch_el.checked);
      lspz_settings.setItem(key, switch_el.checked);
    });
  }
  lspz_settings.registerSetting("master_volume", 50);
  // let volume = localStorage.getItem("master_volume");
  let volume = lspz_settings.getItem("master_volume");

  if (volume) {
    console.log(`Restore user's volume preference to ${volume}`);
    vol_slider.value = volume;
  }
  setVolumeLevels(vol_slider.value);

  vol_slider.addEventListener("input", (e) => {
    console.debug(`master volume to ${vol_slider.value}`);
    setVolumeLevels(vol_slider.value);
    lspz_settings.setItem("master_volume", vol_slider.value);
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

  ["a", "b"].forEach(letter => {
    var input_el = document.getElementById(`input_vocal_${letter}`);
    var input_detail = document.getElementById(`input_vocal_${letter}_detail`);

    input_el.value = 0;
    input_el.max = vocal_amounts.length -1;

    let upfunc = () => {
      let val = input_el.value;
      let desc = vocal_amounts[val];
      input_detail.innerHTML = desc;
    }
    input_el.addEventListener("input", upfunc);
    upfunc();
  });

  lspz_settings.addCallback("show_track_details", (val) => {
    ["a", "b"].forEach(letter => {
      if (val) {
        jQuery(`#collapse-sample-${letter}`).collapse("show");
      } else {
        jQuery(`#collapse-sample-${letter}`).collapse("hide");
      }
    });
  }, true);

  jQuery("#lspz-data-submission").submit(function (e) {
    e.preventDefault();
    jQuery("#lspz-data-submission .btn[type='submit']").html("Submitting...");
    jQuery("#lspz-data-submission .btn[type='submit']").toggleClass(["btn-primary", "btn-outline-primary"]);

    let form = jQuery(this),
        url = form.attr("action");

    let formData = new FormData(document.getElementById("lspz-data-submission"));
    formData.append("a", player_a.track_id);
    formData.append("b", player_b.track_id);
    // let form_data = objectifyForm(jQuery("#lspz-data-submission").serializeArray());
    // console.log(form_data);

    // disable inputs: must happen AFTER grabbing form data
    jQuery("#lspz-data-submission input").prop('disabled', true);
    jQuery("#lspz-data-submission button[type='submit']").prop('disabled', true);

    jQuery.ajax({
      url: url,
      type: "POST",
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

  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
  const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))
}

window.addEventListener("load", lspz_loaded);

function lspz_load_samples() {
  player_a.mark_loading();
  player_b.mark_loading();

  // jQuery.get("/api/v1/random/tracks/2", (data) => {
  jQuery.get("/api/v1/random/connecting_v1", (data) => {
    let trackid_a = data[0];
    let trackid_b = data[1];

    player_a.load_track(trackid_a);
    player_b.load_track(trackid_b);
  });
}

function lspz_reset_page() {
  // firefox would by default restore the form inputs, so clear them first:
  jQuery("#lspz-data-submission")[0].reset();
  window.location.reload();
}
