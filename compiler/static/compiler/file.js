window.onload = function() {
  reloadChooseFile();
};


function reloadChooseFile() {
    const href = '/compiler/display_choose_file/';

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // Add the CSRF token to the headers
    $.ajax({
        url: href,
        type: 'GET',
        headers: {
            'X-CSRF-TOKEN': csrfToken
        },
    })
        .done(function (data) {
            $('#choose-file-text').html(data);
            resetDisplayFormListeners();
        });
}

function displayForm(event) {
    event.preventDefault(); // prevent the link from navigating to a new page

    const href = event.target.href + '/';
    // Get the CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // Add the CSRF token to the headers
    $.ajax({
        url: href,
        type: 'GET',
        headers: {
            'X-CSRF-TOKEN': csrfToken
        },
    })
        .done(function (data) {
            $('#file-form-div').html(data);
            const submitButton = document.getElementById('file-form-btn');
            submitButton.textContent = event.target.textContent;
            const form = document.getElementById('file-form');
            form.action = href;
        });
}

function resetDisplayFormListeners() {
    const menuLinks = $('#file-action a');
    menuLinks.off('click', displayForm); // Remove previous event listeners
    menuLinks.on('click', displayForm); // Add new event listeners
}

$(document).on('submit', '#file-form', function (e) {
    e.preventDefault();

    // Get the form data
    const formData = new FormData(this);

    // Make an AJAX request
    $.ajax({
        url: this.action,
        method: this.method,
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            reloadChooseFile();
            $("#file-form").remove();
        },
        error: function (error) {
            console.error('Error:', error);
        }
    });
});

// Initial setup
$(document).ready(function () {
    resetDisplayFormListeners();
});
