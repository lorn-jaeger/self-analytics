// background.js

let activeTab = null;
let activeTabStartTime = null;

// helper function to get the current timestamp
function getCurrentTime() {
  return new Date().getTime();
}

// function to send POST request to the server
function sendPostRequest(tabInfo) {
  fetch('http://localhost:8080/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tabInfo)
  }).catch((error) => {
    console.error('Error sending data:', error);
  });
}

// function to handle activation of a new tab
function activateTab(tabId, windowId) {
  // if there's an active tab, deactivate it
  if (activeTab !== null) {
    const endTime = getCurrentTime();
    const duration = endTime - activeTabStartTime;
    
    const tabInfo = {
      tabId: activeTab.id,
      url: activeTab.url,
      openTime: activeTabStartTime,
      closeTime: endTime,
      activeDuration: duration
    };
    
    sendPostRequest(tabInfo);
    activeTab = null;
    activeTabStartTime = null;
  }

  // activate the new tab
  browser.tabs.get(tabId).then((tab) => {
    activeTab = tab;
    activeTabStartTime = getCurrentTime();
  }).catch((error) => {
    console.error('Error getting tab information:', error);
  });
}

// function to handle window focus changes
function handleWindowFocusChanged(windowId) {
  if (windowId === browser.windows.WINDOW_ID_NONE) {
    // all browser windows have lost focus, deactivate the active tab
    if (activeTab !== null) {
      const endTime = getCurrentTime();
      const duration = endTime - activeTabStartTime;
      
      const tabInfo = {
        tabId: activeTab.id,
        url: activeTab.url,
        openTime: activeTabStartTime,
        closeTime: endTime,
        activeDuration: duration
      };
      
      sendPostRequest(tabInfo);
      activeTab = null;
      activeTabStartTime = null;
    }
  } else {
    // a window has gained focus, activate its active tab
    browser.tabs.query({active: true, windowId: windowId}).then((tabs) => {
      if (tabs.length > 0) {
        activateTab(tabs[0].id, windowId);
      }
    }).catch((error) => {
      console.error('Error querying active tabs:', error);
    });
  }
}

// function to handle tab removal
function handleTabRemoved(tabId, removeInfo) {
  if (activeTab && activeTab.id === tabId) {
    const endTime = getCurrentTime();
    const duration = endTime - activeTabStartTime;
    
    const tabInfo = {
      tabId: activeTab.id,
      url: activeTab.url,
      openTime: activeTabStartTime,
      closeTime: endTime,
      activeDuration: duration
    };
    
    sendPostRequest(tabInfo);
    activeTab = null;
    activeTabStartTime = null;
  }
}

// event listener for tab activation
browser.tabs.onActivated.addListener((activeInfo) => {
  activateTab(activeInfo.tabId, activeInfo.windowId);
});

// event listener for window focus changes
browser.windows.onFocusChanged.addListener(handleWindowFocusChanged);

// event listener for tab removal
browser.tabs.onRemoved.addListener(handleTabRemoved);

// initialize active tab on extension startup
browser.tabs.query({active: true, currentWindow: true}).then((tabs) => {
  if (tabs.length > 0) {
    activeTab = tabs[0];
    activeTabStartTime = getCurrentTime();
  }
}).catch((error) => {
  console.error('Error initializing active tab:', error);
});
