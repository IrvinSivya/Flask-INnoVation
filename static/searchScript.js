$(document).ready(function() {
  let timeoutId;

  console.log("LOADED LOADED LOADED LOADED")

  $('#search-bar').on('input', function() {
      const skill_searched = $(this).val();
      console.log("SKILL SEARCHED SKILL SEARCHED SKILL SEARCHED:    " + skill_searched)

      // Clear the previous timeout if there is one
      clearTimeout(timeoutId);

      // Set a new timeout to avoid sending too many requests
      timeoutId = setTimeout(function() {
          if (skill_searched.length > 0) {
              $.ajax({
                  url: "/searchTutors",
                  data: { skill_searched: skill_searched },
                  success: function(data) {
                      $('#tutor-container').html(data); // Update the table body with new results
                  }
              });
          } 
          else {
              //$('#tutor-container').html('');
            window.location.href = '/getTutors';
          }
      }, 300); //300 ms delay
  });
});