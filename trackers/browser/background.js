// background.js

let activeTab = null;
let activeTabStartTime = null;

function getCurrentTime() {
  return new Date().getTime();
}

function sendPostRequest(tabInfo) {
  fetch('http://localhost:8080/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tabInfo)
  }).catch((error) => {
    console.error('Error sending data:', error);
  });
}

function getDomain(url) {
  try {
    let urlObj = new URL(url);
    return urlObj.hostname;
  } catch (e) {
    console.error('Invalid URL:', url);
    return url;
  }
}

function activateTab(tabId, windowId) {
  if (activeTab !== null) {
    const endTime = getCurrentTime();
    const duration = endTime - activeTabStartTime;

    const tabInfo = {
      tabId: activeTab.id,
      domain: getDomain(activeTab.url),
      openTime: activeTabStartTime,
      closeTime: endTime,
      activeDuration: duration
    };

    sendPostRequest(tabInfo);
    activeTab = null;
    activeTabStartTime = null;
  }

  browser.tabs.get(tabId).then((tab) => {
    activeTab = tab;
    activeTabStartTime = getCurrentTime();
  }).catch((error) => {
    console.error('Error getting tab information:', error);
  });
}

function handleWindowFocusChanged(windowId) {
  if (windowId === browser.windows.WINDOW_ID_NONE) {
    if (activeTab !== null) {
      const endTime = getCurrentTime();
      const duration = endTime - activeTabStartTime;

      const tabInfo = {
        tabId: activeTab.id,
        domain: getDomain(activeTab.url),
        openTime: activeTabStartTime,
        closeTime: endTime,
        activeDuration: duration
      };

      sendPostRequest(tabInfo);
      activeTab = null;
      activeTabStartTime = null;
    }
  } else {
    browser.tabs.query({ active: true, windowId: windowId }).then((tabs) => {
      if (tabs.length > 0) {
        activateTab(tabs[0].id, windowId);
      }
    }).catch((error) => {
      console.error('Error querying active tabs:', error);
    });
  }
}

function handleTabRemoved(tabId, removeInfo) {
  if (activeTab && activeTab.id === tabId) {
    const endTime = getCurrentTime();
    const duration = endTime - activeTabStartTime;

    const tabInfo = {
      tabId: activeTab.id,
      domain: getDomain(activeTab.url),
      openTime: activeTabStartTime,
      closeTime: endTime,
      activeDuration: duration
    };

    sendPostRequest(tabInfo);
    activeTab = null;
    activeTabStartTime = null;
  }
}

function handleTabUpdated(tabId, changeInfo, tab) {
  if (activeTab && tabId === activeTab.id && changeInfo.url) {
    const oldDomain = getDomain(activeTab.url);
    const newDomain = getDomain(changeInfo.url);

    if (oldDomain !== newDomain) {
      // Domain has changed, send POST request
      const endTime = getCurrentTime();
      const duration = endTime - activeTabStartTime;

      const tabInfo = {
        tabId: activeTab.id,
        domain: oldDomain,
        openTime: activeTabStartTime,
        closeTime: endTime,
        activeDuration: duration
      };

      sendPostRequest(tabInfo);

      // Update activeTab's URL and reset the start time
      activeTab.url = changeInfo.url;
      activeTabStartTime = endTime;
    } else {
      // Update the URL in activeTab without resetting the timer
      activeTab.url = changeInfo.url;
    }
  }
}

browser.tabs.onActivated.addListener((activeInfo) => {
  activateTab(activeInfo.tabId, activeInfo.windowId);
});

browser.windows.onFocusChanged.addListener(handleWindowFocusChanged);

browser.tabs.onRemoved.addListener(handleTabRemoved);

browser.tabs.onUpdated.addListener(handleTabUpdated);

browser.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
  if (tabs.length > 0) {
    activeTab = tabs[0];
    activeTabStartTime = getCurrentTime();
  }
}).catch((error) => {
  console.error('Error initializing active tab:', error);
});
