// Does time stepping left/right based on satellite timestamps if they exists
import { filteredSatelliteTimeList, state } from '../store';

function changeTime(direction: -1 | 1) {
    if (state.satellite.satelliteImagesOn) { // Jump to the next timestmap within an hour of the current one
        const currentIndex = filteredSatelliteTimeList.value.findIndex((item) => item.timestamp === state.satellite.satelliteTimeStamp);
        const currentImageTime = new Date(`${state.satellite.satelliteTimeStamp}Z`);
        console.log(currentIndex);
        // Now we go from the current index and find the Next Day in either direction
        let newTime = null;
        let checkDateIndex = currentIndex + direction * 1
        while (newTime === null && currentIndex !== -1 && checkDateIndex >= 0) {
            const checkTimeString = filteredSatelliteTimeList.value[checkDateIndex].timestamp;
            const checkTime = new Date(`${checkTimeString}Z`);
            const diffTime = Math.abs(checkTime.getTime() - currentImageTime.getTime());
            const diffDays = Math.ceil(diffTime / (60 * 60 * 24));
            if (diffDays >= 1) {
                newTime = checkTime;
            } else {
                checkDateIndex = checkDateIndex + direction * 1;
            }
        }
        if (newTime !== null) {
            state.timestamp = (newTime.valueOf() / 1000.0);
        }
    } else {
        // satellite Images are on we change by day then
        const newTime = state.timestamp + ((60 * 60 * 24) * direction)
        const currentTime =  (Date.now().valueOf() / 1000.0)
        if (newTime >= state.timeMin && newTime <= currentTime ) {
            state.timestamp = newTime;
        } else if (newTime >= currentTime) {
            state.timestamp  = currentTime;
        } else {
            state.timestamp = state.timeMin;
        }
    }
}

export {
    changeTime,
}