function createCookie(name, value, hours) {
    var expires = "";
    if (hours) {
        var date = new Date();
        date.setTime(date.getTime() + (hours * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + value + expires + "; path=/";
}

function deleteCookie(name) {
    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}

window.addEventListener('beforeunload', function() {
  deleteCookie('file_id');
});

function submitTabs(event) {
    if (event)
        event.preventDefault(); // prevent the link from navigating to a new page
    const form = document.getElementById("tab_forms");

    // Get the CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // Add the CSRF token to the headers
    let req = $.ajax({
        url: "/compiler/compile/",
        type: 'POST',
        headers: {
            'X-CSRF-TOKEN': csrfToken
        },
        data: $(form).serialize()
    })

    req.done(function (data) {
        $('#asm-text').html(data);
    })
}


function chooseFile(event) {
    event.preventDefault(); // prevent the link from navigating to a new page
    const fileId = event.target.id.replace('file', '');
    deleteCookie("file_id");
    createCookie("file_id", fileId, 5);
    displayFileText(undefined);
    submitTabs(undefined);
}

function displayFileText(event) {
    const href = "/compiler/file/"
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
            $('#file-text').html(data);
        });
}

function downloadAsm(event) {
    event.preventDefault();
    const href = event.target.href;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // Add the CSRF token to the headers
      $.ajax({
    url: href,
    type: 'GET',
    headers: {
      'X-CSRF-TOKEN': csrfToken
    },
    xhrFields: {
      responseType: 'blob' // Set the response type to 'blob' to handle binary data
    },
    success: function(data) {
        // Create a temporary URL for the downloaded file
      const url = window.URL.createObjectURL(new Blob([data]));

      // Create a temporary <a> element to trigger the file download
      const downloadLink = document.createElement('a');
      downloadLink.href = url;
      downloadLink.setAttribute('download', ''); // Specify the file should be downloaded
      downloadLink.style.display = 'none';
      document.body.appendChild(downloadLink);

      // Trigger the click event to start the file download
      downloadLink.click();

      // Clean up the temporary URL and <a> element
      window.URL.revokeObjectURL(url);
      document.body.removeChild(downloadLink);
    }
  });
}


